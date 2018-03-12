import csv

METADATA_TNAH_FN="/Users/mrgecko/Documents/Dev/Data/Chartes-TNAH/theses/theses.csv"
METADATA_FN="/Users/mrgecko/Documents/Dev/Data/theses/theses.csv"

FINAL_METADATA_FN="/Users/mrgecko/Documents/Dev/Data/theses/theses.csv"

def validator():
    with open(METADATA_TNAH_FN, newline='') as tnah_f,\
         open(METADATA_FN, newline='') as f, \
         open(FINAL_METADATA_FN, mode='w+', newline='') as ff:

        tnah_reader = csv.DictReader(tnah_f, delimiter=',', quotechar='"', dialect="unix")
        reader = csv.DictReader(f, delimiter=',', quotechar='"', dialect="unix")

        rows=[]
        for i, l in enumerate(reader):
            t = next(tnah_reader)
            l["authorKey"] = t["authorKey"]
            l["authorRef"] = t["authorRef"]
            l["ppn_position"] = t["ppn_position"]
            l["ppn_these"] = t["ppn_these"]
            l["an_these"] = t["an_these"]
            rows.append(l)

        csv.register_dialect('positions', quoting=csv.QUOTE_ALL)

        writer = csv.DictWriter(ff, fieldnames=reader.fieldnames, dialect="positions")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    validator()
