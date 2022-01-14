from collections import namedtuple
from pathlib import Path
import re

AUTHORS_TSV_HEADER = "author\tgenres"
MusicAuthorInfo = namedtuple("MusicAuthorInfo", "name genres")


class Gallery:
    def __init__(self, content_dir, authors_info=None):
        if not isinstance(authors_info, dict):
            authors_info = tcv2authors(Path(content_dir) / "authors.tsv")
        print(authors_info)
        self.authors = authors_info
        self.content_dir = Path(content_dir)

    def update_list_of_authors(self):
        for author in (a.name for a in (self.content_dir/"all").iterdir()):
            print(author)
            if author not in self.authors:
                self.authors[author] = None
        print(self.authors)

    def updatu_authors_info(self):
        for author, info in list(self.authors.items()):
            self.authors[author] = info or get_info_from_wikipedia(author)
            self.save()

    def save(self):
        table = [AUTHORS_TSV_HEADER]
        for author, info in self.authors.items():
            if info:
                table.append('\t'.join([author, ', '.join(info.genres)]))
        with (self.content_dir / "authors.tsv").open("wt") as f:
            f.write("\n".join(table))

def tcv2authors(table_path):
    table = Path(table_path).open().read().rstrip('\n').split("\n")
    assert table[0] == AUTHORS_TSV_HEADER
    data = (row.split("\t") for row in table[1:])
    return {n: MusicAuthorInfo(n, [g.strip() for g in g.split(",")]) for n, g in data}

def get_info_from_wikipedia(name):
    import wikipedia
    print(f"wiki {name}")
    try:
        page = wikipedia.page(name + '(band)')
    except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
        return MusicAuthorInfo(name, [])
    html = page.html()
    try:
        i = html.index('Genres</th><td')
        j = html.index('</td>', i)
    except ValueError:
        return MusicAuthorInfo(name, [])
    genres = list(map(lambda s: s.split('=')[1].strip('"'), re.findall(r'title="[^"]*"', html[i:j])))
    print(page.title, genres)
    return MusicAuthorInfo(page.title, genres)
