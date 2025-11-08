import psycopg

conn = None

def openConnection (dbName, username):
    global conn
    conn = psycopg.connect(f'dbname={dbName} user={username}')

def closeConnection ():
    conn.commit()
    conn.close()

def insertData (tableName, data, fieldNames=None, returnID=True):
    result = []
    with conn.cursor() as cur:
        for row in data.values():
            goodFields = {k: v for k, v in row.items() if fieldNames is None or k in fieldNames}
            query = 'INSERT INTO %s (' + ('%s, ' * (len(goodFields.keys()) - 1)) + '%s) VALUES ('# + ('%s, ' * (len(goodFields.values()) - 1)) + '%s) ' + (' RETURNING id;' if returnID else ';')

            args = [tableName]
            args.extend(list(goodFields.keys()))

            query = query % tuple(args)
            query = query + ('%s, ' * (len(goodFields.values()) - 1)) + '%s) ' + (' RETURNING id;' if returnID else ';')

            args = list(goodFields.values())

            cur.execute(query, tuple(args))
            if returnID:
                result.append(cur.fetchone()[0])
    return result

def updateData (tableName, data, keyFieldName, valFieldName):
    with conn.cursor() as cur:
        for k, v in data.items():
            cur.execute(f'UPDATE {tableName} SET {valFieldName} = %s WHERE {keyFieldName} = %s;', (v, k))

def getData (tableName, fieldNames=None):
    with conn.cursor() as cur:
        cur.execute(f'SELECT {'*' if fieldNames is None else ','.join(fieldNames)} FROM {tableName}')
        return cur.fetchall()

def clearTable (tableName):
    with conn.cursor() as cur:
        cur.execute(f'TRUNCATE TABLE {tableName} CASCADE')
