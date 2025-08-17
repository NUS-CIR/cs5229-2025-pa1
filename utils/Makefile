BUILD_DIR = build
PCAP_DIR = pcaps
LOG_DIR = logs

RUN_SCRIPT = ../../utils/run_exercise.py
ENV_CLEANUP_SCRIPT = ../../utils/environment_cleanup.py

ifndef TOPO
TOPO = topology.json
endif

ifdef DPDK_EXE
run_args += -b $(DPDK_EXE)
endif

all: run

run: build
	sudo python3 $(ENV_CLEANUP_SCRIPT)
	sudo python3 $(RUN_SCRIPT) -t $(TOPO) $(run_args)

stop:
	sudo mn -c
	sudo python3 $(ENV_CLEANUP_SCRIPT)

build: dirs
	cd $(BUILD_DIR); cmake ..; make

dirs:
	mkdir -p $(BUILD_DIR) $(PCAP_DIR) $(LOG_DIR)

clean: stop
	rm -f *.pcap
	rm -rf $(BUILD_DIR) $(PCAP_DIR) $(LOG_DIR)
