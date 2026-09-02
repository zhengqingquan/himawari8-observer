"""
进度条
"""


def progressbar(filled, duration, frac, extra=""):
    print(
        "\r",
        "🍅" * filled + "--" * (duration - filled),
        "[{:.0%}]".format(frac),
        extra,
        end="",
    )
