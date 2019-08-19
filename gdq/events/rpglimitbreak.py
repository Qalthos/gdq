import pyplugs

from gdq.events import GDQTracker


@pyplugs.register
class RPGLimitBreak(GDQTracker):
    url = "https://www.rpglimitbreak.com/tracker"
    event = "rpglb"
    stream_ids = ("2019",)
    records = sorted([
        (46595, "RPGLB 2015"),
        (75194.33, "RPGLB 2016"),
        (111773.56, "RPGLB 2017"),
        (164099.31, "RPGLB 2018"),
        (200339.84, "RPGLB 2019"),
    ])
