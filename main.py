import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
import pygame
os.environ['KIVY_GRAPHICS'] = 'gles'

import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse

class GameBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

class ArcadeGameSpace(Widget):
    ball = ObjectProperty(None)
    score_text = StringProperty("Score: 0")
    game_over_text = StringProperty("")
    
    # Spike Animation Properties
    spike_growth = NumericProperty(20) 
    
    game_state = "PLAYING"
    gravity = -0.35          # Constant falling speed like Flappy Bird
    jump_power = 8.5         # Upward flap strength
    score = 0
    
    # Timer tracking for the 4-second grow/shrink pulse loop
    pulse_timer = 0

    def init_game(self):
        self.score = 0
        self.score_text = "Score: 0"
        self.game_over_text = ""
        self.spike_growth = 20 
        self.pulse_timer = 0
        
        self.ball.center_x = self.center_x
        self.ball.center_y = self.center_y
        self.ball.velocity_x = random.choice([-3, 3])
        self.ball.velocity_y = 0
        self.game_state = "PLAYING"

    def update(self, dt):
        if self.game_state != "PLAYING":
            return

        # 1. Pulsing Spikes Logic Loop (Grow for 2s, Shrink for 2s)
        self.pulse_timer += dt
        if self.pulse_timer > 4.0:
            self.pulse_timer = 0.0  # Reset loop every 4 seconds
            
        # First 2 seconds: Grow up to double size (from 20 to 40)
        if self.pulse_timer <= 2.0:
            self.spike_growth = 20 + (self.pulse_timer / 2.0) * 20
        # Next 2 seconds: Shrink back to normal size (from 40 down to 20)
        else:
            self.spike_growth = 40 - ((self.pulse_timer - 2.0) / 2.0) * 20

        # 2. Physics / Gravity Drop (Flappy Bird Movement)
        self.ball.velocity_y += self.gravity
        self.ball.move()

        # Score increases automatically the longer you survive the spikes
        self.score += 1
        if self.score % 10 == 0:
            self.score_text = f"Score: {self.score // 10}"

        # 3. Collision Detection on All 4 Spiked Edges
        # Constant testing against the dynamic pulsing thickness of the spikes
        current_spike_edge = self.spike_growth
        if (self.ball.x <= self.x + current_spike_edge or 
            self.ball.right >= self.right - current_spike_edge or 
            self.ball.top >= self.top - current_spike_edge or
            self.ball.y <= self.y + current_spike_edge):  # Bottom Spike Check
            
            self.game_state = "GAME_OVER"
            self.game_over_text = "GAME OVER!\nTap Screen to Restart"
            self.ball.velocity = (0, 0)

    def move_player(self, direction):
        if self.game_state == "PLAYING":
            self.ball.x += direction * 18

    def trigger_jump(self):
        if self.game_state == "PLAYING":
            # Direct flap override (allows mid-air jumps anytime like Flappy Bird)
            self.ball.velocity_y = self.jump_power

    def on_touch_down(self, touch):
        if self.game_state == "GAME_OVER":
            self.init_game()
            return True
        return super(ArcadeGameSpace, self).on_touch_down(touch)

class MobileInterfaceApp(App):
    def build(self):
        root_canvas = BoxLayout(orientation='vertical')
        self.game_view = ArcadeGameSpace()
        
        with self.game_view.canvas.before:
            Color(0.06, 0.06, 0.1, 1) 
            self.bg_rect = Rectangle(size=self.game_view.size, pos=self.game_view.pos)
            
        with self.game_view.canvas:
            Color(1, 0.25, 0.25, 1) # Red Spikes
            self.top_spike = Rectangle()
            self.left_spike = Rectangle()
            self.right_spike = Rectangle()
            self.bottom_spike = Rectangle() # New bottom spikes canvas element
            
            Color(1, 0.75, 0, 1) # Yellow Player Ball
            self.ball_render = Ellipse()

        self.game_view.bind(size=self.sync_canvas_dimensions, pos=self.sync_canvas_dimensions)
        
        # Ball scale size expanded to (50, 50) making it significantly bigger
        self.game_view.ball = GameBall(size=(50, 50))
        self.game_view.add_widget(self.game_view.ball)

        # Bottom UI controls docks (Inverted directions)
        control_deck = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10, padding=10)
        d_pad_cluster = BoxLayout(orientation='horizontal', spacing=10, size_hint_x=0.6)
        
        btn_left_button = Button(text="LEFT", font_size='18sp', background_color=(0.4, 0.4, 0.4, 1))
        btn_left_button.bind(on_press=lambda instance: self.game_view.move_player(-1))
        
        btn_right_button = Button(text="RIGHT", font_size='18sp', background_color=(0.4, 0.4, 0.4, 1))
        btn_right_button.bind(on_press=lambda instance: self.game_view.move_player(1))
        
        d_pad_cluster.add_widget(btn_left_button)
        d_pad_cluster.add_widget(btn_right_button)

        btn_action_jump = Button(text="JUMP / FLAP", font_size='18sp', size_hint_x=0.4, background_color=(0, 0.55, 1, 1))
        btn_action_jump.bind(on_press=lambda instance: self.game_view.trigger_jump())

        control_deck.add_widget(d_pad_cluster)
        control_deck.add_widget(btn_action_jump)

        root_canvas.add_widget(self.game_view)
        root_canvas.add_widget(control_deck)

        Clock.schedule_interval(self.game_view.update, 1.0 / 60.0)
        Clock.schedule_interval(self.sync_canvas_labels, 1.0 / 60.0)
        Clock.schedule_once(lambda dt: self.game_view.init_game(), 0.1)

        return root_canvas

    def sync_canvas_dimensions(self, instance, value):
        self.bg_rect.pos = self.game_view.pos
        self.bg_rect.size = self.game_view.size
        self.update_spikes()

    def update_spikes(self):
        growth = self.game_view.spike_growth
        
        # Syncing positions dynamically for all 4 borders
        self.top_spike.pos = (self.game_view.x, self.game_view.top - growth)
        self.top_spike.size = (self.game_view.width, growth)
        
        self.left_spike.pos = (self.game_view.x, self.game_view.y)
        self.left_spike.size = (growth, self.game_view.height)
        
        self.right_spike.pos = (self.game_view.right - growth, self.game_view.y)
        self.right_spike.size = (growth, self.game_view.height)
        
        self.bottom_spike.pos = (self.game_view.x, self.game_view.y)
        self.bottom_spike.size = (self.game_view.width, growth)
        
        self.ball_render.pos = self.game_view.ball.pos
        self.ball_render.size = self.game_view.ball.size

    def sync_canvas_labels(self, dt):
        self.update_spikes()
        self.game_view.canvas.ask_update()

    from kivy.lang import Builder
    Builder.load_string('''
<ArcadeGameSpace>:
    Label:
        text: root.score_text
        font_size: '22sp'
        color: 1, 1, 1, 1
        top: root.top - 50
        right: root.right - 50
        size_hint: None, None
        size: self.texture_size
    Label:
        text: root.game_over_text
        font_size: '32sp'
        halign: 'center'
        color: 1, 0.3, 0.3, 1
        center: root.center
        size_hint: None, None
        size: self.texture_size
''')

if __name__ == '__main__':
    MobileInterfaceApp().run()
