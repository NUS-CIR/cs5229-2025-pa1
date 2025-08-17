CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -g
LDFLAGS = -pthread -lrt

TARGET  = secret_util
SRCS    = secret_util.c

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGET)