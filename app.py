from flask import Flask, render_template, request, Response
from seo_analyzer import analyze_seo
import csv
import io
from datetime import datetime

app = Flask(__name__)


def normalize_url(url):
    """
    Adds https:// if user enters example.com instead of https://example.com
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    return url


def generate_csv_report(result):
    """
    Converts SEO result dictionary into CSV text.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Section", "Metric", "Value", "Status", "Message"])

    if not result["success"]:
        writer.writerow(["Error", "Error", result.get("error"), "Error", "SEO analysis failed"])
        return output.getvalue()

    writer.writerow(["Overall", "URL", result["url"], "", ""])
    writer.writerow(["Overall", "Final URL", result["final_url"], "", ""])
    writer.writerow(["Overall", "Status Code", result["status_code"], "", ""])
    writer.writerow(["Overall", "Response Time", result["response_time"], "", "seconds"])
    writer.writerow(["Overall", "SEO Score", result["score"]["score"], result["score"]["grade"], ""])

    writer.writerow([
        "Title",
        "Title Text",
        result["title"]["title"],
        result["title"]["status"],
        result["title"]["message"]
    ])

    writer.writerow([
        "Title",
        "Title Length",
        result["title"]["length"],
        result["title"]["status"],
        ""
    ])

    writer.writerow([
        "Meta Description",
        "Description",
        result["meta"]["description"],
        result["meta"]["status"],
        result["meta"]["message"]
    ])

    writer.writerow([
        "Meta Description",
        "Description Length",
        result["meta"]["length"],
        result["meta"]["status"],
        ""
    ])

    for tag, data in result["headings"]["headings"].items():
        writer.writerow([
            "Headings",
            tag.upper(),
            data["count"],
            result["headings"]["status"],
            result["headings"]["message"]
        ])

    writer.writerow(["Links", "Total Links", result["links"]["total_links"], "", ""])
    writer.writerow(["Links", "Internal Links", result["links"]["internal_count"], "", ""])
    writer.writerow(["Links", "External Links", result["links"]["external_count"], "", ""])
    writer.writerow(["Links", "Empty Links", result["links"]["empty_count"], "", ""])

    writer.writerow([
        "Images",
        "Total Images",
        result["images"]["total_images"],
        result["images"]["status"],
        result["images"]["message"]
    ])

    writer.writerow([
        "Images",
        "Missing Alt Text",
        result["images"]["missing_alt_count"],
        result["images"]["status"],
        ""
    ])

    writer.writerow([
        "Images",
        "Empty Alt Text",
        result["images"]["empty_alt_count"],
        result["images"]["status"],
        ""
    ])

    writer.writerow([
        "Canonical",
        "Canonical URL",
        result["canonical"]["url"],
        result["canonical"]["status"],
        result["canonical"]["message"]
    ])

    writer.writerow([
        "Robots Meta",
        "Content",
        result["robots_meta"]["content"],
        result["robots_meta"]["status"],
        result["robots_meta"]["message"]
    ])

    writer.writerow([
        "Open Graph",
        "Found Tags",
        result["open_graph"]["found_count"],
        result["open_graph"]["status"],
        result["open_graph"]["message"]
    ])

    for tag, data in result["open_graph"]["tags"].items():
        writer.writerow([
            "Open Graph",
            tag,
            "Found" if data["found"] else "Missing",
            "",
            data["content"] if data["content"] else ""
        ])

    writer.writerow([
        "Structured Data",
        "JSON-LD Blocks",
        result["structured_data"]["count"],
        result["structured_data"]["status"],
        result["structured_data"]["message"]
    ])

    writer.writerow([
        "Site Files",
        "robots.txt",
        "Found" if result["site_files"]["robots_txt"]["found"] else "Missing",
        "",
        result["site_files"]["robots_txt"]["url"]
    ])

    writer.writerow([
        "Site Files",
        "sitemap.xml",
        "Found" if result["site_files"]["sitemap_xml"]["found"] else "Missing",
        "",
        result["site_files"]["sitemap_xml"]["url"]
    ])

    for recommendation in result["recommendations"]:
        writer.writerow([
            "Recommendations",
            "Suggestion",
            recommendation,
            "",
            ""
        ])

    return output.getvalue()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")

        if not url:
            return render_template("index.html", error="Please enter a URL.")

        url = normalize_url(url)
        result = analyze_seo(url)

        return render_template("result.html", result=result)

    return render_template("index.html")


@app.route("/download-csv")
def download_csv():
    url = request.args.get("url")

    if not url:
        return "URL is required", 400

    url = normalize_url(url)
    result = analyze_seo(url)

    csv_data = generate_csv_report(result)

    filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# debug=True is only for local development.
if __name__ == "__main__":
    app.run(debug=True)