from CatLampPY import CommandErrorMsg
from tables import getTimes
times = getTimes()


def parseTime(time: float, unit: str):
    """Shared function to calculate string time to a time integer."""
    if time <= 0:
        time = 1
    # Unit checking
    if unit.lower() in times:
        time = times[unit.lower()] * time
    else:
        raise CommandErrorMsg("Invalid time unit!")
    return time
