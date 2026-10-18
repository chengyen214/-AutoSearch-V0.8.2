"""
database/migrate.py

AutoSearch V4

Database Migration Manager


功能:

1. 建立 Database Schema

2. 執行 Migration

3. Migration History Tracking


支援:

V2.5
    - Article Database


V3
    - AI Analysis Database


V4 P1
    - Knowledge Archive
    - AI Task Queue
    - Knowledge Ranking


V4 P2.2
    - Search Index Optimization

"""


from database.connection import get_connection

from utils.logger import logger






# ======================================
# Migration Files
# ======================================


MIGRATION_FILES = [


    "database/schema.sql",


    "database/migration_v4_p1_1.sql",


    "database/migration_v4_p1_2.sql",


    "database/migration_v4_p1_5.sql",


    "database/migration_v4_p2_2.sql",
    
    "database/migration_v4_p2_2_5.sql",

    # P2.2.2 Archive Version History
    "database/migration_v4_p2_2_2.sql",
    
    "database/migration_v4_p2_4_1.sql",

    # ======================================
    # V5.1 P1.2
    # User Target
    # ======================================

    "database/migration_v5_p1_2.sql",
    
    # ======================================
    # V5.4 P4.2
    # Job Repository
    # ======================================

    "database/migration_v5_p4_2.sql",

    # ======================================
    # V6 P6.1
    # Target Crawler URL
    # ======================================

    "database/migration_v6_p6_1.sql",
    "database/migration_v6_p6_2.sql",
    "database/migration_v6_p6_3.sql",
    "database/migration_v6_p6_4.sql",
    "database/migration_v6_p6_5.sql",
    "database/migration_v9_p5_1.sql"

]








# ======================================
# Migration History Table
# ======================================


def create_migration_table(cursor):


    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS migration_history

        (

            id INT AUTO_INCREMENT PRIMARY KEY,


            filename VARCHAR(255) NOT NULL UNIQUE,


            executed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """

    )









# ======================================
# Check Migration
# ======================================


def migration_executed(

    cursor,

    filename

):


    cursor.execute(

        """

        SELECT id

        FROM migration_history

        WHERE filename = %s

        """,

        (

            filename,

        )

    )



    result = cursor.fetchone()



    return result is not None







# ======================================
# Record Migration
# ======================================


def record_migration(

    cursor,

    filename

):


    cursor.execute(

        """

        INSERT INTO migration_history

        (

            filename

        )

        VALUES

        (

            %s

        )

        """,

        (

            filename,

        )

    )









# ======================================
# Execute SQL File
# ======================================


def execute_sql_file(

    cursor,

    filepath

):


    logger.info(

        f"Loading migration: {filepath}"

    )



    with open(

        filepath,

        "r",

        encoding="utf-8"

    ) as f:


        sql = f.read()





    statements = sql.split(";")





    for statement in statements:


        statement = statement.strip()



        if statement:


            cursor.execute(

                statement

            )









# ======================================
# Migration
# ======================================


def migrate():



    conn = get_connection()



    if conn is None:


        raise Exception(

            "Database connection failed."

        )





    cursor = conn.cursor()






    try:



        # create history table first

        create_migration_table(

            cursor

        )






        for migration in MIGRATION_FILES:




            try:



                if migration_executed(

                    cursor,

                    migration

                ):



                    logger.info(

                        f"Skip executed migration: {migration}"

                    )


                    continue






                execute_sql_file(

                    cursor,

                    migration

                )






                record_migration(

                    cursor,

                    migration

                )






                logger.info(

                    f"Completed: {migration}"

                )






            except FileNotFoundError:



                logger.warning(

                    f"Skip missing migration: {migration}"

                )








        conn.commit()





        logger.info(

            "Database migration complete"

        )





        print()

        print(

            "================================="

        )

        print(

            " Database Migration Complete"

        )

        print(

            "================================="

        )








    except Exception as e:



        conn.rollback()



        logger.error(

            f"Migration failed: {e}"

        )



        raise






    finally:



        cursor.close()


        conn.close()











if __name__ == "__main__":


    migrate()