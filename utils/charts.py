import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io


def bar_chart(labels, values, title, color="#2196F3"):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


def pie_chart(labels, values, title):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    ax.set_title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


def line_chart(x, y, title, xlabel="", ylabel=""):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, marker="o", color="#2196F3")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


def grouped_bar_chart(labels, values1, values2, label1, label2, title):
    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(labels))
    ax.bar([i - 0.2 for i in x], values1, width=0.4, label=label1, color="#2196F3")
    ax.bar([i + 0.2 for i in x], values2, width=0.4, label=label2, color="#F44336")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45)
    ax.legend()
    ax.set_title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf
