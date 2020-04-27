A command line tool to download tv shows from sdarot website

- Capable of downloading specific episodes or entire seasons
- Fetching search results if not sure what the tv show is
- Downloaded files can be named both in Hebrew and English

### Usage

```cmd
Usage: main.py [OPTIONS] TV_SHOW

  This script will download tv shows from sdarot tv website TV_SHOW is the
  name of the tv show to download

Options:
  --seasons TEXT        Seasons to download, divided by comma
  --download-path TEXT  Set the downlaod path, by default download path is set
                        to Download folder
  -h, --help            Show this message and exit.

```

### Examples

Example for the search:

```cmd
python main.py Avatar
Select TV show to download
[x] Avatar The Last Airbender - *בבודמ* - ןורחאה ריוואה ףשכ :ראטווא (2005)
[ ] Avatar The Legend Of Korra - הרוק לש הדגאה :ראטווא (2015)
[ ] Avatar The Legend of Korra - HebDub - *בבודמ* הרוק לש הדגאה :ראטווא (2015)
[ ] Avatar The Last Airbender HebSub - ןורחאה ריוואה ףשכ :ראטווא (2005)
[ ] Exit
```

Example for downloading a TV show:

