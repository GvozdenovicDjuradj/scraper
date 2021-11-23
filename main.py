from tsd_scraper import TdsScraper
from tv_program_scraper import TVProgramScraper
from apscheduler.schedulers.blocking import BlockingScheduler
import xmltodict


def daily_scraper():
    tds_scraper = TdsScraper()
    tds_scraper.scrap()

    tv_program_scraper = TVProgramScraper()
    tv_program_scraper.scrap()

    output_dict = {"tv": {}}
    output_dict["tv"]["channel"] = tds_scraper.channels + tv_program_scraper.channels
    output_dict["tv"]["programme"] = tds_scraper.epgs + tv_program_scraper.epgs

    with open("/app/output/all_channels_epgs.xml", "w") as f:
        f.write(xmltodict.unparse(output_dict, pretty=True))

    # path used for testing
    # with open("/home/djura/Desktop/tsd.xml", "w") as f:
    #     f.write(xmltodict.unparse(output_dict, pretty=True))


daily_scraper()
scheduler = BlockingScheduler()

# daily job. Executes every morning at 07:01:01s
job_daily = scheduler.add_job(func=daily_scraper, coalesce=True, misfire_grace_time=100, args=[],
                              max_instances=2, trigger="cron", year="*", month="*", day="*", hour=7, minute=1, second=1)

# job used for testing
# job_daily = scheduler.add_job(func=daily_scraper, misfire_grace_time=100, args=[], coalesce=True,
#                               max_instances=1, trigger="cron", year="*", month="*", day="*", hour="*", minute="*",
#                               second="*")

scheduler.start()
