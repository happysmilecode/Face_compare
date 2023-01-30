
def writelog(log):
    f = open('./log.txt', 'a')
    if type(log) == str:
        strLog = log
    else:
        strLog = str(log)

    f.write(strLog)
    f.close()