from datetime import datetime
import requests
from bs4 import BeautifulSoup


class TdsScraper:
    # list of all epgs
    epgs = []

    # list of all channels
    channels = []

    def __init__(self):
        self.raw_html_url = "https://tsd-tv.com/programska-sema/"

        # only one channel. Adds it to list
        self.channels.append({
            "@id": "TELEVIZIJA SRPSKE DIJASPORE",
            "display-name":
                {
                    "@lang": "sl",
                    "#text": "TELEVIZIJA SRPSKE DIJASPORE"
                },
            "icon": {"@src": ""},
            "url": "https://tsd-tv.com"
        })

    def scrap(self):
        # extract raw html
        raw_html = requests.get(self.raw_html_url)
        html_content = BeautifulSoup(raw_html.text, 'html.parser')

        # list of all timestamps, one par day
        days_timestamps = [int(elem.get("data-date")) for elem in html_content.find_all("div", class_="extvs-date-day")]

        # template request. Used to retrieve data for each day
        url = 'https://tsd-tv.com/wp-admin/admin-ajax.php'
        body = {
            "action": "extvs_get_schedule_simple",
            "chanel": "tsd",
            "date": 0
        }

        # counter :D
        count = -1

        # first loop. Iterates over timestamps, retrieves and parses data for that day
        for timestamp in days_timestamps:
            # sets date parameter of the template request
            body["date"] = timestamp

            # extracts row html data for current day
            raw_html_day = requests.post(url, data=body).json()["html"]
            html_content_day = BeautifulSoup(raw_html_day, 'html.parser')

            # extracts raw list of all epgs from the html
            epgs_raw = html_content_day.find_all("tr", class_="extvs-past-progr")

            # second loop. Iterates over raw epgs and parses them
            for ind, epg_raw in enumerate(epgs_raw):

                # ... if they exist
                if epg_raw is not None:

                    # image info
                    image = epg_raw.find("img")
                    image_src = epg_raw.find("img").get("src") if image is not None else None

                    # extracts time and minute of epg start: [<hour_of_start>, <minute_of_start>]
                    time_list = epg_raw.find("td", class_="extvs-table1-time").find("span").text.split(":")

                    # create object from current timestamp(iterator)
                    dt_object = datetime.fromtimestamp(timestamp)

                    # set time to represent time of epg start
                    dt_object = dt_object.replace(hour=int(time_list[0]), minute=int(time_list[1]))

                    # translate to timestamp and subtract one hour to match desired timezone
                    dt_timestamp = int(dt_object.timestamp()) - 3600

                    # translate back to object
                    dt_object = datetime.fromtimestamp(dt_timestamp)

                    # title info
                    title = epg_raw.find("h3").text

                    # if epg is the last one in the list set its end time, else leave it empty
                    if ind == len(epgs_raw) - 1:

                        # create epg dict for the last epg
                        epg = {
                            "@start": dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2],
                            # last epg always last for 5 minutes
                            # -1 hour to match the desired timezone
                            "@stop": dt_object.replace(hour=int(time_list[0]) - 1,
                                                       minute=int(time_list[1]) + 5).strftime("%Y%m%d%H%M%S +%f")[:-2],

                            "@channel": "TELEVIZIJA SRPSKE DIJASPORE",
                            "title": {"@lang": "sl", "#text": title},
                            "desc": {"@lang": "sl"},
                            "date": dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2][:4],
                            "icon": {"@src": image_src}

                        }
                    else:
                        # create epg dict for all other epgs
                        epg = {
                            "@start": dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2],
                            "@stop": None,
                            "@channel": "TELEVIZIJA SRPSKE DIJASPORE",
                            "title": {"@lang": "sl", "#text": title},
                            "desc": {"@lang": "sl"},
                            "date": dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2][:4],
                            "icon": {"@src": image_src}

                        }

                    # if epg is not the first one set end time of the previous one to start time of the current one
                    if ind > 0:
                        # end time of previous epg is the star time of the current one
                        self.epgs[count]["@stop"] = dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2]

                    # append all epgs to epgs list
                    self.epgs.append(epg)
                    count += 1
