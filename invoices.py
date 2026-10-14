from flask import Flask, request
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        c = canvas.Canvas("invoice.pdf", pagesize=LETTER)
        text = c.beginText(40, 750)

        for k, v in request.form.items():
            text.textLine(f"{k}: {v}")

        c.drawText(text)
        c.showPage()
        c.save()

        return "Invoice generated"

    return """
    <form method="post">
        <input name="customer" placeholder="Customer"><br>
        <input name="amount" placeholder="Amount"><br>
        <button type="submit">Generate</button>
    </form>
    """

if __name__ == "__main__":
    app.run(debug=True)
