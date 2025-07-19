from machine import Pin, SPI
import framebuf
import utime


EPD_WIDTH = 200
EPD_HEIGHT = 200

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

SPI_INTERFACE = 1


class EPD_1in54_B_V2:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.spi = SPI(SPI_INTERFACE)
        self.spi.init(baudrate=4000000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer_black = bytearray([0XFF] * (self.height * self.width // 8))
        self.buffer_red = bytearray([0XFF] * (self.height * self.width // 8))
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        print("reset")
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(10)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        while (self.digital_read(self.busy_pin) == 1):
            self.delay_ms(100)
        print('busy release')

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(500)
        self.ReadBusy()
        self.delay_ms(500)
        self.send_command(0x12)
        self.delay_ms(500)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal
        self.delay_ms(500)

        self.send_command(0x01)  # Driver output control
        self.send_data(0xC7)
        self.send_data(0x00)
        self.send_data(0x01)
        self.delay_ms(500)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x01)
        self.delay_ms(500)

        self.send_command(0x44)  # set Ram-X address start/end position
        self.send_data(0x00)
        self.send_data(0x18)  # 0x18-->(24+1)*8=200
        self.delay_ms(500)

        self.send_command(0x45)  # set Ram-Y address start/end position
        self.send_data(0xC7)  # 0xC7-->(199+1)=200
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.delay_ms(500)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)
        self.delay_ms(500)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)
        self.delay_ms(500)

        self.send_command(0x4E)   # set RAM x address count to 0
        self.send_data(0x00)
        self.send_command(0x4F)   # set RAM y address count to 0X199
        self.send_data(0xC7)
        self.send_data(0x00)
        self.delay_ms(500)
        self.ReadBusy()
        self.delay_ms(500)
        return 0

    def display(self):
        if self.width%8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        buf = [0x00] * self.height * linewidth

        # send black data
        if (self.buffer_black != None):
            self.send_command(0x24) # DATA_START_TRANSMISSION_1
            self.send_data1(self.buffer_black)
                
        # send red data        
        if (self.buffer_red != None):
            self.send_command(0x26) # DATA_START_TRANSMISSION_2
            for i in range(0, int(self.width * self.height / 8)):
                buf[i] = ~self.buffer_red[i]
            self.send_data1(buf)

        self.send_command(0x22) # DISPLAY_REFRESH
        self.send_data(0xF7)
        self.send_command(0x20) # DISPLAY_REFRESH
        self.ReadBusy()

    def Clear(self):
        if self.width % 8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        self.send_command(0x24)  # DATA_START_TRANSMISSION_1
        self.send_data1([0xff] * int(self.height * linewidth))

        self.send_command(0x26)  # DATA_START_TRANSMISSION_2
        self.send_data1([0x00] * int(self.height * linewidth))

        self.send_command(0x22)  # DISPLAY_REFRESH
        self.send_data(0xF7)
        self.send_command(0x20)  # DISPLAY_REFRESH
        self.ReadBusy()

    def sleep(self):
        self.send_command(0X10)
        self.send_data(0x01)

        self.delay_ms(2000)
        self.module_exit()


if __name__ == '__main__':
    epd = EPD_1in54_B_V2()
    epd.Clear()
    epd.imageblack.fill(0xff)
    epd.imagered.fill(0xff)
    epd.imageblack.text("Waveshare", 0, 10, 0x00)
    epd.imagered.text("ePaper-1.54", 0, 25, 0x00)
    epd.imageblack.text("RPi Pico", 0, 40, 0x00)
    epd.imagered.text("Hello World", 0, 55, 0x00)
    epd.display()
    epd.delay_ms(2000)

    epd.imagered.vline(10, 90, 40, 0x00)
    epd.imagered.vline(90, 90, 40, 0x00)
    epd.imageblack.hline(10, 90, 80, 0x00)
    epd.imageblack.hline(10, 130, 80, 0x00)
    epd.imagered.line(10, 90, 90, 130, 0x00)
    epd.imageblack.line(90, 90, 10, 130, 0x00)
    epd.display()
    epd.delay_ms(2000)

    epd.imageblack.rect(10, 150, 40, 40, 0x00)
    epd.imageblack.fill_rect(60, 150, 40, 40, 0x00)
    epd.display()
    epd.delay_ms(2000)

    epd.Clear()
    epd.delay_ms(2000)
    print("sleep")
    epd.sleep()
    print("complete")
