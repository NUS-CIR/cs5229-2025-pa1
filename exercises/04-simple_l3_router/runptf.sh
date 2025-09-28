#! /bin/bash

sudo ./../../utils/veth_setup.sh
sudo python3 ../../utils/environment_cleanup.py

T="`realpath ../../testlib`"
if [ x"${PYTHONPATH}" == "x" ]
then
    P="${T}"
else
    P="${T}:${PYTHONPATH}"
fi

mkdir -p ./out

pushd ./out
cmake ..
make
popd 

PROGRAM_NAME=$(basename "$(pwd)")
PROGRAM_NAME="${PROGRAM_NAME#*-}"

set -x
sudo ./out/$PROGRAM_NAME \
    --proc-type=auto  \
    --no-pci  \
    --vdev=net_tap0,iface=tap0 \
    --vdev=net_tap1,iface=tap1 \
    --vdev=net_tap2,iface=tap2 \
    --vdev=net_tap3,iface=tap3 \
    --vdev=net_tap4,iface=tap4 \
    --vdev=net_tap5,iface=tap5 \
    --vdev=net_tap6,iface=tap6 \
    --vdev=net_tap7,iface=tap7 \
    -l 0-1 -n2 > ./out/$PROGRAM_NAME.log 2>&1 &
echo ""
echo "Started $PROGRAM_NAME.  Waiting 2 seconds before starting PTF test ..."
sleep 2

set +x
for i in `seq 0 7`
do
    sudo ovs-vsctl add-br br$i
    sudo ovs-vsctl add-port br$i tap$i
    sudo ovs-vsctl add-port br$i veth$(expr $i \* 2)
    sudo ovs-ofctl add-flow br$i in_port=2,actions=output:1
    sudo ovs-ofctl add-flow br$i in_port=1,actions=output:2
done

set -x
sudo `which ptf` \
    --pypath "$P" \
    -i 0@veth1 \
    -i 1@veth3 \
    -i 2@veth5 \
    -i 3@veth7 \
    -i 4@veth9 \
    -i 5@veth11 \
    -i 6@veth13 \
    -i 7@veth15 \
    --test-dir ptf

echo ""
echo "PTF test finished.  Waiting 2 seconds before killing $PROGRAM_NAME ..."
sleep 2
sudo pkill --signal 9 --list-name $PROGRAM_NAME
echo ""
echo "Verifying that there are no $PROGRAM_NAME processes running any longer in 4 seconds ..."
sleep 4
ps axguwww | grep $PROGRAM_NAME

set +x
for i in `seq 0 7`
do
    sudo ovs-vsctl del-br br$i
done

set -x
/bin/rm -rf ./out
/bin/rm -rf ./ptf.log ./ptf.pcap

sudo ./../../utils/veth_teardown.sh
sudo python3 ../../utils/environment_cleanup.py