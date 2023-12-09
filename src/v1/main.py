from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color
from viewport import Viewport
import time

import hitman

try:
    from androidtoast import toast
    TOASTER = True
except ModuleNotFoundError:
    print("Not on an android device.")
    TOASTER = False


class BackgroundLabel(Label):
    def on_pos(self, *args):
        self.canvas.before.clear() # type: ignore
        with self.canvas.before: # type: ignore
            Color(0, 0, 1, 0.25)
            Rectangle(pos=self.pos, size=self.size)
            
    def on_size(self, *args):
        self.canvas.before.clear() # type: ignore
        with self.canvas.before: # type: ignore
            Color(0, 0, 1, 0.25)
            Rectangle(pos=self.pos, size=self.size)


global last_time
last_time = time.time()


class MainApp(App):
    def build(self):
        self.root = Viewport(size=(1080, 3480))
        
        self.main_layout = FloatLayout()
        
        self.parent_box = BoxLayout(orientation="vertical")
        self.parent_box.size_hint = (0.75, 0.75)
        
        self.label_item = Label(
            text="Enter a phone number:",
            font_size="20dp",
            size_hint=(1.25, 0.0625),
            pos_hint={"center_x": 0.5, "top":1}
        )
        self.parent_box.add_widget(self.label_item)
        
        self.input_group = RelativeLayout()
        self.input_group.size_hint = (1.0, 0.0625)
        self.input_group.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        
        self.textbox_item = TextInput(
            multiline=False, 
            readonly=False, 
            halign="center",
            font_size=0,
            text="",
            size_hint=(0, 0),
            opacity=0,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.textbox_item.bind(text=self.text_changed) # type: ignore
        self.fake_display = BackgroundLabel(
            text="< CLICK HERE >",
            font_size="20dp",
            size_hint=(1.0, 0.3125),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        #self.fake_display.bind(on_touch_up=self.open_input) # type: ignore
        self.fake_display.bind(on_touch_down=self.open_input) # type: ignore
        self.input_group.add_widget(self.textbox_item)
        self.input_group.add_widget(self.fake_display)
        
        self.parent_box.add_widget(self.input_group)
        
        self.hit_button = ToggleButton(
            font_size="16dp",
            text="ACTIVATE",
            size_hint=(0.6, 0.0625),
            pos_hint={"center_x": 0.5, "bottom": 1.0}
        )
        self.hit_button.bind(on_press=self.on_hitman_toggle) # type: ignore
        self.parent_box.add_widget(self.hit_button)
        
        self.report_box = Label(
            text="<no data, if you are seeing this, please report an issue>",
            font_size="12dp",
            halign="justify",
            size_hint=(1.0, 1.0),
            pos_hint={"center_x": 0.5, "bottom":1}
            )
        self.parent_box.add_widget(self.report_box)
        
        self.parent_box.pos_hint={"center_x": 0.5, "center_y": 0.5}
        self.main_layout.add_widget(self.parent_box)

        Clock.schedule_interval(self.update_report, 1.0)

        self.root.add_widget(self.main_layout)
        return self.root


    def text_changed(self, _instance, text):
        self.fake_display.text = text


    def open_input(self, _label_instance, touch_event):
        self.textbox_item.focus = True
        FocusBehavior.ignored_touch.append(touch_event)


    def on_hitman_send(self, _button_instance):
        global last_time
        new_time = time.time()
        if ((new_time - last_time) >= 3):
            last_time = new_time
            number = self.fake_display.text
            print(_msg:="Hit sent for", number)
            if TOASTER:
                toast(text=_msg, short_duration=True)
            hitman.execute(number)
        else:
            print(_msg:="still on timeout.")
            toast(text=_msg, short_duration=True)
            
    
    def on_hitman_toggle(self, toggle_button_instance):
        state = toggle_button_instance.state
        if (state == 'normal'):
            print("stopped")
            hitman.stop_execution_toggle()
        if (state == 'down'):
            print("started")
            hitman.start_execution_toggle(self.fake_display.text)


    def update_report(self, _time):
        self.report_box.text = hitman.get_data()



def main():
    app = MainApp()
    app.run()


if __name__ == '__main__':
    main()
