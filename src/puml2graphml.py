import argparse
import sys

from pc.pc_version import VERSION

SUPPORTED_LANGUAGES = {"en": "en_US", "ru": "ru_RU"}

LANGUAGE = "en_US"


def process_cmdline() -> int:
    parser = argparse.ArgumentParser(
        prog="puml2graphml", usage="%(prog)s [options]\npuml2graphml {}".format(VERSION)
    )
    parser.add_argument("infile", nargs="?", type=str)
    parser.add_argument("outfile", nargs="?", type=str)
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="compile to JSON object file instead of GRAPHML",
    )
    parser.add_argument(
        "--list-lang",
        action="store_true",
        help="list supported languages and exit",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        help="language code to use (default: en)",
    )

    args = parser.parse_args()

    if args.list_lang:
        if args.infile or args.outfile or args.json:
            print(
                "Error: --list-lang must not be combined with other arguments.",
                file=sys.stderr,
            )
            return 1
        print("Supported languages:")
        for lang in SUPPORTED_LANGUAGES:
            print(f" - {lang}")
        return 0

    if args.lang not in SUPPORTED_LANGUAGES:
        print(
            f"Error: unsupported language '{args.lang}'. Supported languages are: {', '.join(SUPPORTED_LANGUAGES)}",
            file=sys.stderr,
        )
    global LANGUAGE
    LANGUAGE = SUPPORTED_LANGUAGES[args.lang]

    if not args.infile or not args.outfile:
        parser.error("You must specify both infile and outfile.")

    from pc.errorlog.error import StackedErrorContext

    ec = StackedErrorContext(ofile=sys.stderr)
    from pc.puml_compiler import puml_compiler

    res, jsonres = puml_compiler(args.infile, ec, args.json)
    if not res:
        with open(args.outfile, "wt", encoding="utf8") as f:
            f.write(jsonres)
    return res


if __name__ == "__main__":
    sys.exit(process_cmdline())
