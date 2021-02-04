from typing import NamedTuple

from flask import Flask, render_template, url_for


class Job(NamedTuple):
    id: int
    name: str
    status: str


class Detection(NamedTuple):
    id: int
    report_type: str
    start: int
    stop: int
    video_path: str


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def index():
    return render_template("index.html", msg="Gjoevik")


@app.route("/projects")
def projects_page():
    jobs = [
        Job(**{"id": i, "name": f"Test{i}", "status": "Pending"})
        for i in range(1, 100)
    ]

    return render_template("projects.html", jobs=jobs)


@app.route("/projects/new")
def new_project_page():
    hello()
    hello = "Hello, World!"

    return render_template("new.html")


@app.route("/report")
def report_page():
    detections = [
        Detection(
            **{
                "id": i,
                "report_type": f"Type{i}",
                "start": "Now",
                "stop": "Later",
                "video_path": "C:\\",
            }
        )
        for i in range(1, 100)
    ]

    return render_template("result.html", detections=detections)


@app.route("/image")
def image():

    return render_template("image.html")


if __name__ == "__main__":
    app.run(debug=True)


def noncompliant():
    foo()  # Noncompliant
    foo = sum

    func()  # Noncompliant

    def func():
        pass

    MyClass()  # Noncompliant

    class MyClass:
        pass
