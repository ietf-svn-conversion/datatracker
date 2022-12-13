export DEBIAN_FRONTEND=noninteractive

echo "Fixing permissions..."
chmod -R 777 ./

echo "Ensure all requirements.txt packages are installed..."
pip --disable-pip-version-check --no-cache-dir install -r requirements.txt

echo "Creating data directories..."
chmod +x ./docker/scripts/app-create-dirs.sh
./docker/scripts/app-create-dirs.sh

mkdir -p pgdata

# Setup pg database container
echo "Setting up PostgreSQL DB container..."
docker run -d --name pgdb -p 5432:5432 \
    -e POSTGRES_PASSWORD=RkTkDPFnKpko \
    -e POSTGRES_USER=django \
    -e POSTGRES_DB=ietf \
    -e POSTGRES_HOST_AUTH_METHOD=trust \
    -v ./pgdata:/var/lib/postgresql/data \
    postgres:14.5

# Add Postgresql Apt Repository to get 14    
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Install pg client and pgloader
apt-get update
apt-get install -y --no-install-recommends postgresql-client-14 pgloader

# Copy settings files
cp ./docker/configs/settings_local.py ./ietf/settings_local.py
cp ./docker/configs/settings_mysqldb.py ./ietf/settings_mysqldb.py
cp ./docker/configs/settings_postgresqldb.py ./ietf/settings_postgresqldb.py

# Wait for DB containers
echo "Waiting for DB containers to come online..."
/usr/local/bin/wait-for db:3306 -- echo "MariaDB ready"
/usr/local/bin/wait-for pgdb:5432 -- echo "Postgresql ready"

# Initial checks
echo "Running initial checks..."
/usr/local/bin/python ./ietf/manage.py check --settings=settings_local

# The mysql database is always freshly build container from the 
# image build of last-night's dump when this script is run
# The first run of migrations will run anything merged from main that
# that hasn't been released, and the few pre-engine-shift migrations
# that the feat/postgres branch adds. It is guaranteed to fail at
# utils.migrations.0004_pause_to_change_database_engines (where it
# fails on purpose, hence the `|| true` so we may proceed
/usr/local/bin/python ./ietf/manage.py migrate --settings=settings_local || true

cat ./ietf/settings_local.py | sed 's/from ietf.settings_mysqldb import DATABASES/from ietf.settings_postgresqldb import DATABASES/' > /tmp/settings_local.py && mv /tmp/settings_local.py ./ietf/settings_local.py

# Now transfer the migrated database from mysql to postgres unless that's already happened.
echo "Transferring migrated database from MySQL to PostgreSQL..."
EMPTY_CHECK=`psql -U django -h pgdb -d ietf -c "\dt" 2>&1`
if echo ${EMPTY_CHECK} | grep -q "Did not find any relations."; then
    cat << EOF > cast.load
LOAD DATABASE
FROM mysql://django:RkTkDPFnKpko@db/ietf_utf8
INTO postgresql://django:RkTkDPFnKpko@pgdb/ietf
CAST type varchar to text drop typemod;
EOF
    time pgloader --verbose --logfile=ietf_pgloader.run --summary=ietf_pgloader.summary cast.load
    rm cast.load
    /usr/local/bin/python ./ietf/manage.py migrate --settings=settings_local
else
    echo "The postgres database is in an unexpected state"
    echo ${EMPTY_CHECK}
fi

# Stop postgreSQL container
echo "Stopping PostgreSQL container..."
docker stop pgdb

echo "Done."
