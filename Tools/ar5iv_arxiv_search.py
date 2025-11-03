# Ar5iv/arxiv search

from lxml import etree
from lxml import html
import json
import requests


def parse_ar5iv_html(html_text: str) -> dict:
    tree = etree.HTML(html_text)
    result = {}

    title_el = tree.xpath("//h1[contains(@class, 'ltx_title_document')]")
    title = title_el[0].xpath(".//text()") if title_el else []
    result["title"] = " ".join([t.strip() for t in title if t.strip()])

    authors = tree.xpath("//div[contains(@class, 'ltx_authors')]//span[contains(@class, 'ltx_personname')]")
    result["authors"] = ["".join(a.itertext()).strip() for a in authors if "".join(a.itertext()).strip()]

    abstract_nodes = tree.xpath("//div[contains(@class, 'ltx_abstract')]//p")
    abstract_text = ["".join(p.itertext()).strip() for p in abstract_nodes if "".join(p.itertext()).strip()]
    result["abstract"] = "\n".join(abstract_text)

    sections = []
    section_nodes = tree.xpath("//section[contains(@class, 'ltx_section')]")
    for sec in section_nodes:
        heading = sec.xpath("./*[self::h2 or self::h3 or self::h4][1]")
        if not heading:
            continue
        section_title = "".join(heading[0].itertext()).strip()
        if section_title.lower().startswith("references"):
            continue

        subsection_nodes = sec.xpath(".//section[contains(@class, 'ltx_subsection')]")
        para_texts = []

        if subsection_nodes:
            for sub in subsection_nodes:
                sub_heading = sub.xpath("./*[self::h3 or self::h4 or self::h5][1]")
                sub_title = "".join(sub_heading[0].itertext()).strip() if sub_heading else ""
                sub_paras = sub.xpath(".//div[contains(@class, 'ltx_para')]")
                for para in sub_paras:
                    text = "".join(para.itertext()).strip()
                    if text:
                        para_texts.append(f"{sub_title}: {text}" if sub_title else text)
        else:
            # if there are no subsections, gets paragraphs directly under section
            paras = sec.xpath(".//div[contains(@class, 'ltx_para')]")
            for para in paras:
                text = "".join(para.itertext()).strip()
                if text:
                    para_texts.append(text)

        if para_texts:
            sections.append({
                "section_title": section_title,
                "paragraphs": para_texts
            })

    result["sections"] = sections
    return result


def parse_arxiv_html(html_text: str) -> dict:
    tree = etree.HTML(html_text)
    result = {}

    title_el = tree.xpath("//h1[contains(@class, 'title')]")
    title = title_el[0].xpath(".//text()") if title_el else []
    result["title"] = " ".join([t.strip() for t in title if t.strip() and t.strip() != "Title:"])

    authors = tree.xpath("//div[contains(@class, 'authors')]//a")
    result["authors"] = [a.text.strip() for a in authors if a.text and a.text.strip()]

    abstract_el = tree.xpath("//blockquote[contains(@class, 'abstract')]")
    abstract_text = abstract_el[0].xpath(".//text()") if abstract_el else []
    abstract_clean = " ".join([t.strip() for t in abstract_text if t.strip() and t.strip() != "Abstract:"])
    result["abstract"] = abstract_clean

    return result


def extract_arxiv_ids_from_text(xml_text):
    tree = etree.fromstring(xml_text.encode("utf-8"))
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    ids = [el.text.strip() for el in tree.xpath("//atom:entry/atom:id", namespaces=ns)]
    return [i.split("/abs/")[-1] for i in ids]


def ar5iv_search(query: str, top_k: int = 5) -> list:
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={top_k}"
    # headers = {
    # "User-Agent": "Mozilla/5.0 (Yashwanth/1.0) FastMCP Bot"
    #             }
    response = requests.get(url)  # , headers=headers)
    ids = extract_arxiv_ids_from_text(response.text)
    # ids.append("2412.18979") # For testing

    results = []
    for id in ids:
        ar5iv_url = f"https://ar5iv.org/abs/{id}"
        response_ar5iv = requests.get(ar5iv_url)
        if 'content="article"' in response_ar5iv.text:
            print(f"Using ar5iv for {id}")
            parsed = parse_ar5iv_html(response_ar5iv.text)
        else:
            print(f"Falling back to arXiv HTML for {id}")
            arxiv_html = requests.get(f"https://arxiv.org/abs/{id}").text
            parsed = parse_arxiv_html(arxiv_html)

        parsed["id"] = id
        results.append(parsed)

    return results


if __name__ == "__main__":
    output_path = "test.json"
    data = ar5iv_search("Electronic Structure and Vibrational Stability of Copper-substituted Lead Apatite (LK-99) Cabezas-Escares 2024", top_k=2)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Parsed data written to: {output_path}")
