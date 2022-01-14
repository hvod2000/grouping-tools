from collections import namedtuple, defaultdict
from pathlib3x import Path # from pathlib import Path
import re
import wikipedia

AUTHORS_TSV_HEADER = "author\tgenres"
MusicAuthorInfo = namedtuple("MusicAuthorInfo", "name genres")


class Gallery:
    def __init__(self, content_dir, authors_info=None):
        if not isinstance(authors_info, dict):
            authors_info = tcv2authors(Path(content_dir) / "authors.tsv")
        print(authors_info)
        self.authors = authors_info
        self.content_dir = Path(content_dir)

    @staticmethod
    def from_mess_without_any_info(messy_dir):
        content_dir = Path(messy_dir)
        if (content_dir / "authors.tsv").is_file():
            return Gallery(content_dir)
        authors = list(sorted(content_dir.iterdir()))
        (content_dir / "all").mkdir()
        for author in authors:
            author.rename(content_dir / "all" / author.name)
        with (content_dir / "authors.tsv").open("wt") as f:
            f.write(AUTHORS_TSV_HEADER)
        return Gallery(content_dir, {})

    def update_list_of_authors(self):
        for author in (a.name for a in (self.content_dir / "all").iterdir()):
            print(author)
            if author not in self.authors:
                self.authors[author] = None
        print(self.authors)

    def update_authors_info(self):
        for author, info in list(self.authors.items()):
            self.authors[author] = info or get_info_from_wikipedia(author)
            self.save()

    def save(self):
        table = [AUTHORS_TSV_HEADER]
        genres = defaultdict(set)
        for author, info in sorted(self.authors.items()):
            if info:
                table.append("\t".join([author, ", ".join(info.genres)]))
                for g in info.genres:
                    genres[g].add(author)
        with (self.content_dir / "authors.tsv.part").open("wt") as f:
            f.write("\n".join(table))
        the_dir = self.content_dir
        (the_dir / "authors.tsv.part").rename(the_dir / "authors.tsv")
        linkp = Path("..") / "all"
        for genre, authors in genres.items():
            if (self.content_dir / genre).is_dir():
                (self.content_dir / genre).rmtree()
            (self.content_dir / genre).mkdir()
            for author in authors:
                (the_dir / genre / author).symlink_to(linkp / author)


def tcv2authors(table_path):
    table = Path(table_path).open().read().rstrip("\n").split("\n")
    assert table[0] == AUTHORS_TSV_HEADER
    data = (row.split("\t") for row in table[1:])
    return {n: MusicAuthorInfo(n, g.split(", ") if g else []) for n, g in data}


def get_info_from_wikipedia(name):
    print(f"wiki {name}")
    try:
        page = wikipedia.page(name + "(band)")
    except (
        wikipedia.exceptions.PageError,
        wikipedia.exceptions.DisambiguationError,
    ):
        return MusicAuthorInfo(name, [])
    html = page.html()
    try:
        i = html.index("Genres</th><td")
        j = html.index("</td>", i)
    except ValueError:
        return MusicAuthorInfo(name, [])
    genres = re.findall(r'title="[^"]*"', html[i:j])
    genres = [g.split("=")[1].strip('"').replace('/', '-') for g in genres]
    print(page.title, genres)
    return MusicAuthorInfo(page.title, genres)


if __name__ == "__main__":
    import sys
    g = Gallery.from_mess_without_any_info(sys.argv[1])
    g.update_list_of_authors()
    g.update_authors_info()
    g.save()
