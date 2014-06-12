import json

import MySQLdb



# TODO: use SQLAlchemy if it gets more complicated

#language=SQL
CUSTOMER_QUERY = """
SELECT d.id, d.label, d.title, c.customernumber, c.canonicalname, os.title, dtype.title FROM device AS d
    INNER JOIN contract AS con ON d.contract_id = con.id
    INNER JOIN project AS p ON con.project_id = p.id
    INNER JOIN customer AS c ON p.customer_id = c.id
    LEFT JOIN deviceconfig AS dconf ON dconf.device_id = d.id
    LEFT JOIN devicetypecatalog AS dtype ON d.devicetypecatalog_id = dtype.id
    LEFT JOIN distributioncatalog AS dist ON dconf.distributioncatalog_id = dist.id
    LEFT JOIN oscatalog AS os ON dist.oscatalog_id = os.id
WHERE d.label LIKE %s
"""

#language=SQL
ID_RESOLVE_QUERY = """
SELECT d.id FROM device AS d
WHERE d.label LIKE %s
"""

#language=SQL
CHECK_EXIST_QUERY = """
SELECT d.id, d.deleted, d.contract_id FROM device AS d
WHERE d.label LIKE %s
"""

DEVICE_TYPE_BLACKLIST = (
    "Arbeitsplatzhardware",
    "Beamer",
    "Divers",
    "kundeneigene Hardware",
    "virtueller Eintrag"
)

DEVICE_TYPE_OS_EXPECTED = (
    "Server",
    "V-Server",
    "Virtual Machine"
)


class AssetDBAPI(object):
    def __init__(self, host, user, passwd):
        try:
            self.db_conn = MySQLdb.connect(
                host=host,
                user=user,
                passwd=passwd,
                db="asset_db2",
                connect_timeout=1,
                use_unicode=True,
            )
        except MySQLdb.OperationalError:
            raise RuntimeError("AssetDB MySQL connect failed")

        self.replacements = json.load(open('asset_dbfixes.json'))

    @staticmethod
    def generate_group_name(device_type, os):
        if device_type in DEVICE_TYPE_OS_EXPECTED and not os:
            return "N/A"
        if os:
            return os.strip()
        elif device_type and (device_type.strip() not in DEVICE_TYPE_BLACKLIST):
            return device_type.strip()

    @staticmethod
    def convert_label_to_asset_db(label):
        return int(label, 16)

    @staticmethod
    def convert_label_from_asset_db(label):
        return "%04X" % label

    # TODO: remove redundant code

    def get_device_information(self, clabel=None):
        if not clabel:
            clabel = "%"  # match all
        else:
            clabel = self.convert_label_to_asset_db(clabel)

        try:
            cur = self.db_conn.cursor()
            cur.execute(CUSTOMER_QUERY, [clabel])
            data = cur.fetchall()

            result = []
            for entry in data:
                entry = list(entry)
                for s, d in self.replacements.items():
                    entry[2] = entry[2].lower().replace(s, d)
                result.append(entry)

            return result

        except MySQLdb.OperationalError:
            raise RuntimeError("AssetDB MySQL error")

    def get_id_for_label(self, clabel):
        try:
            cur = self.db_conn.cursor()
            cur.execute(ID_RESOLVE_QUERY, [self.convert_label_to_asset_db(clabel)])
            device = cur.fetchone()

            if device:
                return device[0]
        except MySQLdb.OperationalError:
            raise RuntimeError("AssetDB MySQL error")

    def check_if_label_exists(self, clabel):
        try:
            cur = self.db_conn.cursor()
            cur.execute(CHECK_EXIST_QUERY, [self.convert_label_to_asset_db(clabel)])
            device = cur.fetchone()

            if device:
                if device[1] or not device[2]:
                    return "deleted"
                else:
                    return True

            else:
                # database query returned no results
                return False

        except MySQLdb.OperationalError:
            raise RuntimeError("AssetDB MySQL error")


def main():
    from django.conf import settings

    api = AssetDBAPI(settings.ASSETDB_HOST, settings.ASSETDB_USER,
                     settings.ASSETDB_PASSWORD)

    print api.get_device_information("C92D")
    print api.get_id_for_label("CA98")


if __name__ == '__main__':
    main()


