"""One command: refresh reviews, tag new ones, recompute metrics, answer 'how are our ratings?'."""
import argparse

import metrics
import scrape
import tag


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-scrape", action="store_true")
    p.add_argument("--skip-tag", action="store_true")
    p.add_argument("--tag-limit", type=int, help="tag at most N new reviews (low stars first)")
    a = p.parse_args()
    if not a.skip_scrape:
        scrape.run()
    if not a.skip_tag:
        tag.run(limit=a.tag_limit)
    print()
    print(metrics.format_summary(metrics.write_all()))


if __name__ == "__main__":
    main()
