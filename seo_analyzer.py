import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def fetch_page(url):
    """
    Fetch the webpage HTML and return soup + response info.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        return {
            "success": True,
            "soup": soup,
            "status_code": response.status_code,
            "response_time": round(response.elapsed.total_seconds(), 2),
            "final_url": response.url
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_title(soup):
    """
    Check page title.
    """
    if soup.title and soup.title.text.strip():
        title = soup.title.text.strip()
        length = len(title)

        if length < 30:
            status = "Warning"
            message = "Title is too short."
        elif length > 60:
            status = "Warning"
            message = "Title is too long."
        else:
            status = "Good"
            message = "Title length looks good."

        return {
            "title": title,
            "length": length,
            "status": status,
            "message": message
        }

    return {
        "title": None,
        "length": 0,
        "status": "Error",
        "message": "Title tag is missing."
    }


def check_meta_description(soup):
    """
    Check meta description.
    """
    meta = soup.find("meta", attrs={"name": "description"})

    if meta and meta.get("content"):
        description = meta.get("content").strip()
        length = len(description)

        if length < 70:
            status = "Warning"
            message = "Meta description is too short."
        elif length > 160:
            status = "Warning"
            message = "Meta description is too long."
        else:
            status = "Good"
            message = "Meta description length looks good."

        return {
            "description": description,
            "length": length,
            "status": status,
            "message": message
        }

    return {
        "description": None,
        "length": 0,
        "status": "Error",
        "message": "Meta description is missing."
    }


def check_headings(soup):
    """
    Count H1-H6 headings and collect heading text.
    """
    heading_data = {}

    for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        headings = soup.find_all(tag)
        heading_data[tag] = {
            "count": len(headings),
            "texts": [h.get_text(strip=True) for h in headings if h.get_text(strip=True)]
        }

    h1_count = heading_data["h1"]["count"]

    if h1_count == 0:
        status = "Error"
        message = "No H1 tag found."
    elif h1_count > 1:
        status = "Warning"
        message = "Multiple H1 tags found."
    else:
        status = "Good"
        message = "H1 structure looks good."

    return {
        "headings": heading_data,
        "status": status,
        "message": message
    }


def check_links(soup, url):
    """
    Separate internal and external links.
    """
    domain = urlparse(url).netloc
    links = soup.find_all("a", href=True)

    internal_links = []
    external_links = []
    empty_links = []

    for link in links:
        href = link.get("href").strip()

        if href == "" or href == "#":
            empty_links.append(href)
            continue

        full_url = urljoin(url, href)
        parsed_link = urlparse(full_url)

        if parsed_link.netloc == domain:
            internal_links.append(full_url)
        else:
            external_links.append(full_url)

    return {
        "total_links": len(links),
        "internal_links": internal_links,
        "external_links": external_links,
        "empty_links": empty_links,
        "internal_count": len(internal_links),
        "external_count": len(external_links),
        "empty_count": len(empty_links)
    }


def check_images(soup):
    """
    Check images and missing alt text.
    """
    images = soup.find_all("img")

    missing_alt = []
    empty_alt = []

    for img in images:
        alt = img.get("alt")

        if alt is None:
            missing_alt.append(img.get("src"))
        elif alt.strip() == "":
            empty_alt.append(img.get("src"))

    total_issues = len(missing_alt) + len(empty_alt)

    if len(images) == 0:
        status = "Info"
        message = "No images found."
    elif total_issues == 0:
        status = "Good"
        message = "All images have alt text."
    else:
        status = "Warning"
        message = f"{total_issues} images have missing or empty alt text."

    return {
        "total_images": len(images),
        "missing_alt_count": len(missing_alt),
        "empty_alt_count": len(empty_alt),
        "missing_alt": missing_alt,
        "empty_alt": empty_alt,
        "status": status,
        "message": message
    }
def check_canonical(soup):
    canonical = soup.find("link", rel="canonical")

    if canonical and canonical.get("href"):
        return {
            "found": True,
            "url": canonical.get("href"),
            "status": "Good",
            "message": "Canonical tag found."
        }

    return {
        "found": False,
        "url": None,
        "status": "Warning",
        "message": "Canonical tag is missing."
    }

def check_robots_meta(soup):
    robots = soup.find("meta", attrs={"name": "robots"})

    if robots and robots.get("content"):
        content = robots.get("content").lower()

        if "noindex" in content:
            status = "Error"
            message = "Page has noindex. Search engines may not index this page."
        elif "nofollow" in content:
            status = "Warning"
            message = "Page has nofollow. Search engines may not follow links on this page."
        else:
            status = "Good"
            message = "Robots meta tag looks fine."

        return {
            "found": True,
            "content": content,
            "status": status,
            "message": message
        }

    return {
        "found": False,
        "content": None,
        "status": "Info",
        "message": "No robots meta tag found. Default behavior is usually index/follow."
    }

def check_open_graph(soup):
    og_tags = {
        "og:title": soup.find("meta", property="og:title"),
        "og:description": soup.find("meta", property="og:description"),
        "og:image": soup.find("meta", property="og:image"),
        "og:url": soup.find("meta", property="og:url")
    }

    result = {}

    for tag, element in og_tags.items():
        result[tag] = {
            "found": bool(element and element.get("content")),
            "content": element.get("content") if element and element.get("content") else None
        }

    found_count = sum(1 for item in result.values() if item["found"])

    if found_count == 4:
        status = "Good"
        message = "All important Open Graph tags are present."
    elif found_count >= 2:
        status = "Warning"
        message = "Some Open Graph tags are missing."
    else:
        status = "Warning"
        message = "Most Open Graph tags are missing."

    return {
        "tags": result,
        "found_count": found_count,
        "status": status,
        "message": message
    }

def check_structured_data(soup):
    json_ld_scripts = soup.find_all("script", type="application/ld+json")

    if json_ld_scripts:
        return {
            "found": True,
            "count": len(json_ld_scripts),
            "status": "Good",
            "message": f"{len(json_ld_scripts)} JSON-LD structured data block(s) found."
        }

    return {
        "found": False,
        "count": 0,
        "status": "Info",
        "message": "No JSON-LD structured data found."
    }

def check_site_files(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    files = {
        "robots_txt": f"{base_url}/robots.txt",
        "sitemap_xml": f"{base_url}/sitemap.xml"
    }

    result = {}

    for name, file_url in files.items():
        try:
            response = requests.get(file_url, timeout=5)

            result[name] = {
                "url": file_url,
                "found": response.status_code == 200,
                "status_code": response.status_code
            }

        except requests.exceptions.RequestException:
            result[name] = {
                "url": file_url,
                "found": False,
                "status_code": None
            }

    return result



def calculate_score(results):
    score = 0

    # Title - 15 points
    if results["title"]["status"] == "Good":
        score += 15
    elif results["title"]["status"] == "Warning":
        score += 8

    # Meta description - 15 points
    if results["meta"]["status"] == "Good":
        score += 15
    elif results["meta"]["status"] == "Warning":
        score += 8

    # Headings - 15 points
    if results["headings"]["status"] == "Good":
        score += 15
    elif results["headings"]["status"] == "Warning":
        score += 8

    # Images - 10 points
    if results["images"]["status"] == "Good":
        score += 10
    elif results["images"]["status"] == "Warning":
        score += 5
    elif results["images"]["status"] == "Info":
        score += 7

    # Links - 10 points
    if results["links"]["total_links"] > 0:
        score += 10

    # Canonical - 10 points
    if results["canonical"]["found"]:
        score += 10

    # Robots meta - 10 points
    if results["robots_meta"]["status"] in ["Good", "Info"]:
        score += 10
    elif results["robots_meta"]["status"] == "Warning":
        score += 5

    # Open Graph - 5 points
    if results["open_graph"]["status"] == "Good":
        score += 5
    elif results["open_graph"]["status"] == "Warning":
        score += 2

    # Structured data - 5 points
    if results["structured_data"]["found"]:
        score += 5

    # Site files - 5 points
    if results["site_files"]["robots_txt"]["found"]:
        score += 2
    if results["site_files"]["sitemap_xml"]["found"]:
        score += 3

    if score >= 90:
        grade = "Excellent"
    elif score >= 75:
        grade = "Good"
    elif score >= 50:
        grade = "Needs Improvement"
    else:
        grade = "Poor"

    return {
        "score": score,
        "grade": grade
    }

def generate_recommendations(results):
    recommendations = []

    if results["title"]["status"] != "Good":
        recommendations.append("Improve the title tag. Keep it descriptive, clear, and ideally around 30-60 characters.")

    if results["meta"]["status"] != "Good":
        recommendations.append("Add or improve the meta description. Keep it specific to the page and around 70-160 characters.")

    if results["headings"]["status"] != "Good":
        recommendations.append("Fix heading structure. Use one clear H1 and organize content with H2-H6 headings.")

    if results["images"]["missing_alt_count"] > 0 or results["images"]["empty_alt_count"] > 0:
        recommendations.append("Add descriptive alt text to important images.")

    if not results["canonical"]["found"]:
        recommendations.append("Add a canonical tag to tell search engines the preferred URL for this page.")

    if results["robots_meta"]["status"] == "Error":
        recommendations.append("Remove noindex if this page should appear in search results.")

    if results["open_graph"]["status"] != "Good":
        recommendations.append("Add Open Graph tags to improve social media link previews.")

    if not results["structured_data"]["found"]:
        recommendations.append("Consider adding JSON-LD structured data if the page has business, article, product, or FAQ content.")

    if not results["site_files"]["robots_txt"]["found"]:
        recommendations.append("Add a robots.txt file to guide crawlers.")

    if not results["site_files"]["sitemap_xml"]["found"]:
        recommendations.append("Add a sitemap.xml file to help search engines discover important pages.")

    if not recommendations:
        recommendations.append("Great! No major SEO issues found in this basic audit.")

    return recommendations



def analyze_seo(url):
    page = fetch_page(url)

    if not page["success"]:
        return {
            "success": False,
            "error": page["error"]
        }

    soup = page["soup"]

    results = {
        "success": True,
        "url": url,
        "status_code": page["status_code"],
        "response_time": page["response_time"],
        "final_url": page["final_url"],
        "title": check_title(soup),
        "meta": check_meta_description(soup),
        "headings": check_headings(soup),
        "links": check_links(soup, url),
        "images": check_images(soup),
        "canonical": check_canonical(soup),
        "robots_meta": check_robots_meta(soup),
        "open_graph": check_open_graph(soup),
        "structured_data": check_structured_data(soup),
        "site_files": check_site_files(url)
    }

    results["score"] = calculate_score(results)
    results["recommendations"] = generate_recommendations(results)

    return results
