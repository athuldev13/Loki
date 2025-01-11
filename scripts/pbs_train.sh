#PBS -N GridSearcher-Train
##PBS -l nodes=1:ppn=4
#PBS -l mem=8g
#PBS -l file=10g
## Queues: vshort (10min), short (2h 30min), medium (24h), long (1 week)
#PBS -q medium
#PBS -j oe

# setup
echo "LOKIDIR: ${LOKIDIR}"
source /etc/profile
source $LOKIDIR/setup_dev.sh

# determine path for array job
if [ ! -z ${PBS_ARRAYID} ]; then
	echo "ALGINDEX   : ${ALGINDEX}"
	echo "PBS_ARRAYID: ${PBS_ARRAYID}"
	WSPATH=`sed -n ${PBS_ARRAYID}p ${ALGINDEX}` 
fi 

# determine import flag
IFLAG=""
if [ ! -z ${IMPORTMOD} ]; then
    echo "IMPORT MODULE: ${IMPORTMOD}"
    IFLAG="-i ${IMPORTMOD}"
fi

# execute
echo "WSPATH: ${WSPATH}"
loki ${IFLAG} mv train -f ${WSPATH}

echo "Done"

