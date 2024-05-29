from database import *


def list_arg():
    query = TVcompList.select(TVcompList.name)

    for comp in query.tuples():
        name = str(*comp)
        comp_list = HHCompList.get_or_none(HHCompList.name == name)
        if comp_list:
            query = HHCompList.update({HHCompList.tag: "all"}).where(HHCompList.name == name)
            query.execute()
            print("update:", name)
        else:
            HHCompList.create(name=name, tag="tv")
            print("create:", name)
