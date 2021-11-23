import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime


class TVProgramScraper:
    # list of all epgs
    epgs = []

    # list of all channels
    channels = []

    def __init__(self):
        self.raw_html_url = "https://www.tvprogram.rs/tv-program-danas-svi-kanali.html"

    def scrap(self):
        # dictionary used to group all epgs per channel.
        # Each channel contains list of all epgs that belong to that channel
        epgs_per_channel = {}

        raw_html = requests.get(self.raw_html_url)
        html_content = BeautifulSoup(raw_html.text, 'html.parser')

        # List of all urls, 7 in total, where program per each day can be found
        daily_urls = [elem.find("a").get("href") for elem in
                      html_content.find("a", class_="selected").parent.parent.find_all("li")]

        # current time
        start_timestamp = time.time()

        # current time object
        start_day_obj = datetime.fromtimestamp(start_timestamp)

        # current day object. Current time without hours and minutes
        start_day_obj = start_day_obj.replace(hour=0, minute=0, second=0, microsecond=0)

        # current day timestamp. Timestamp created from start_day_obj object
        current_day_timestamp = start_day_obj.timestamp()

        # first loop. Iterates over programme per each day
        for one_day_url in daily_urls:
            # date object which will be used to represent time in each epg
            current_day_object = datetime.fromtimestamp(current_day_timestamp)

            current_day_timestamp += 86400  # after addition represents the next day

            # collect raw html for current day
            raw_html_day = requests.get(one_day_url)
            html_content_day = BeautifulSoup(raw_html_day.text, 'html.parser')

            # extract programme for current day divided in categories
            all_categories_contents = html_content_day.find_all("div", class_="ruler-wrap clearfix")

            # second loop. Iterates over all categories in current day
            for category_content in all_categories_contents:
                # extract channel names per current category
                all_category_channels = [elem.get_text() for elem in
                                         category_content.find("div", class_="left-part-schedule").find_all("li")]

                # extract programme(content) for current category divided per channels
                all_channels_contents = category_content.find_all("ul", class_="tv-satnica clearfix")

                # third loop. Iterates over all channels in current category
                for channel_ind, channel_content in enumerate(all_channels_contents):
                    # adds channel to dict and channels list if it is not already there
                    if all_category_channels[channel_ind] not in epgs_per_channel:
                        epgs_per_channel[all_category_channels[channel_ind]] = []
                        self.channels.append({
                            "@id": all_category_channels[channel_ind],
                            "display-name":
                                {
                                    "@lang": "sl",
                                    "#text": all_category_channels[channel_ind]
                                },
                            "icon": {"@src": ""},
                            "url": ""
                        })

                    # extracts all epg contents for current channel
                    all_epg_contents = channel_content.find_all("li")

                    # fourth loop. Iterates over all epgs contents in current channel
                    for ind, epg_content in enumerate(all_epg_contents):
                        # extracts epg title from html
                        title = epg_content.find("p").get_text()

                        # extracts time and minute of epg start: [<hour_of_start>, <minute_of_start>]
                        time_list = epg_content.find("div", class_="houre-time").get_text().split(" ")[0].split(":")

                        # html can contain empty placeholder epgs. They will not be considered
                        if len(time_list) == 2:
                            # set time to represent time of epg start
                            current_day_object = current_day_object.replace(hour=int(time_list[0]),
                                                                            minute=int(time_list[1]))

                            # subtract one hour to match desired timezone
                            dt_timestamp = int(current_day_object.timestamp()) - 3600

                            # subtracting one hour can translate object in previous day, therefore new object is created
                            dt_object = datetime.fromtimestamp(dt_timestamp)
                            # create epg dict
                            epg = {
                                "@start": dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2],

                                # this will be added later.
                                # If the epg ends in the next day,
                                # information about exact time will be known in on of the future iterations
                                "@stop": None,

                                "@channel": all_category_channels[channel_ind],
                                "title": {"@lang": "sl", "#text": title},
                                "desc": {"@lang": "sl"},
                                "date": current_day_object.strftime("%Y%m%d%H%M%S +%f")[:-2][:4],
                                "icon": {"@src": None}
                            }

                            # add it to grouped dict
                            epgs_per_channel[all_category_channels[channel_ind]].append(epg)

        # iterates over all created epgs to add missing information about ending time
        for channel_name, epgs in epgs_per_channel.items():
            for i in range(1, len(epgs)):

                # end time of current epg is the star time of the next one
                epgs[i - 1]["@stop"] = epgs[i]["@start"]

                # append all epgs to epgs list
                self.epgs.append(epgs[i - 1])

                if i == len(epgs) - 1:
                    # end time of the last epg is fixed to 06:00h in the day that it started
                    epgs[i]["@stop"] = datetime.strptime(
                        epgs[i]["@start"], "%Y%m%d%H%M%S +%f").replace(
                        hour=5, minute=0).strftime("%Y%m%d%H%M%S +%f")[:-2]

                    # append the last one
                    self.epgs.append(epgs[i])
