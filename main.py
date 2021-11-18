import copy
import traceback
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from xml.dom import minidom
from apscheduler.schedulers.blocking import BlockingScheduler


def daily_scraper():
    raw_html = requests.get("https://tsd-tv.com/programska-sema/")
    html_content = BeautifulSoup(raw_html.text, 'html.parser')
    days_timestamps = [int(elem.get("data-date")) for elem in html_content.find_all("div", class_="extvs-date-day")]

    url = 'https://tsd-tv.com/wp-admin/admin-ajax.php'
    body = {
        "action": "extvs_get_schedule_simple",
        "chanel": "tsd",
        "date": 0
    }

    epgs = []
    count = -1

    for timestamp in days_timestamps:
        body["date"] = timestamp
        raw_html_day = requests.post(url, data=body).json()["html"]

        html_content_day = BeautifulSoup(raw_html_day, 'html.parser')

        epgs_raw = html_content_day.find_all("tr", class_="extvs-past-progr")

        for ind, epg_raw in enumerate(epgs_raw):

            if epg_raw is not None:

                image = epg_raw.find("img")

                image_src = epg_raw.find("img").get("src") if image is not None else None

                time_list = epg_raw.find("td", class_="extvs-table1-time").find("span").text.split(":")

                dt_object = datetime.fromtimestamp(timestamp)
                dt_object = dt_object.replace(hour=int(time_list[0]) - 1, minute=int(time_list[1]))

                title = epg_raw.find("h3").text

                if ind == len(epgs_raw) - 1:
                    epg = dict(
                        icon=image_src,
                        title=title,
                        start=dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2],
                        end=dt_object.replace(hour=int(time_list[0]) - 1, minute=int(time_list[1]) + 5).strftime(
                            "%Y%m%d%H%M%S +%f")[:-2]
                    )
                else:
                    epg = dict(
                        icon=image_src,
                        title=title,
                        start=dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2]
                    )

                if ind > 0:
                    epgs[count]["end"] = dt_object.strftime("%Y%m%d%H%M%S +%f")[:-2]

                epgs.append(epg)
                count += 1

    root = minidom.Document()
    tv = root.createElement('tv')
    root.appendChild(tv)

    channel = root.createElement('channel')
    channel.setAttribute('id', 'TELEVIZIJA SRPSKE DIJASPORE')
    tv.appendChild(channel)

    name = root.createElement('display-name')
    name.setAttribute('lang', 'sl')
    channel.appendChild(name)
    text_name = root.createTextNode("TELEVIZIJA SRPSKE DIJASPORE")
    name.appendChild(text_name)

    icon = root.createElement('icon')
    icon.setAttribute('src', "")
    channel.appendChild(icon)

    url = root.createElement('url')
    channel.appendChild(url)
    text_url = root.createTextNode("https://tsd-tv.com")
    url.appendChild(text_url)

    for epg in epgs:
        programme = root.createElement('programme')
        programme.setAttribute('start', epg["start"])
        programme.setAttribute('stop', epg["end"])
        programme.setAttribute('channel', 'TELEVIZIJA SRPSKE DIJASPORE')
        tv.appendChild(programme)

        title = root.createElement('title')
        title.setAttribute('lang', "sl")
        text_title = root.createTextNode(epg["title"])
        title.appendChild(text_title)
        programme.appendChild(title)

        desc = root.createElement('desc')
        desc.setAttribute('lang', "sl")
        programme.appendChild(desc)

        date = root.createElement('date')
        text_date = root.createTextNode(epg["start"][:4])
        date.appendChild(text_date)
        programme.appendChild(date)

        icon = root.createElement('icon')
        icon.setAttribute('src', epg["icon"])
        programme.appendChild(icon)

    xml_str = root.toprettyxml(indent="\t")
    # with open("/home/djura/Desktop/tsd.xml", "w") as f:
    #     f.write(xml_str)
    with open("/app/output/tsd.xml", "w") as f:
        f.write(xml_str)


daily_scraper()
scheduler = BlockingScheduler()
job_daily = scheduler.add_job(func=daily_scraper, coalesce=True, misfire_grace_time=100, args=[],
                              max_instances=2, trigger="cron", year="*", month="*", day="*", hour=7, minute=1, second=1)

# job_daily = scheduler.add_job(func=daily_scraper, misfire_grace_time=100, args=[], coalesce=True,
#                               max_instances=1, trigger="cron", year="*", month="*", day="*", hour="*", minute="*",
#                               second="*")

scheduler.start()
