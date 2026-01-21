from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
import random
import os

SCORE_FILE = "score.txt"

class ThreeMensMorrisAI(App):
    def build(self):
        self.board = [" "] * 9
        self.player = "X"
        self.ai = "O"
        self.current = None
        self.phase = "place"
        self.move_count = {"X":0,"O":0}
        self.selected_index = None
        self.game_over = False
        self.difficulty = "Medium"
        self.score = {"X":0,"O":0}
        self.load_score()

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # الرسائل
        self.msg_label = Label(text="اختر الوضع أولاً", font_size=22, size_hint=(1,0.1))
        root.add_widget(self.msg_label)

        # شبكة اللعبة
        self.grid = GridLayout(cols=3, spacing=5, size_hint=(1,0.7))
        self.buttons = []
        for i in range(9):
            btn = Button(font_size=48, background_normal='', background_color=(1,1,1,1))
            btn.bind(on_release=partial(self.cell_pressed,i))
            self.grid.add_widget(btn)
            self.buttons.append(btn)
        root.add_widget(self.grid)

        # التحكم
        controls = BoxLayout(size_hint=(1,0.2), spacing=5)
        reset_btn = Button(text="RESET")
        reset_btn.bind(on_release=self.reset)
        diff_btn = Button(text="AI LEVEL")
        diff_btn.bind(on_release=self.choose_level)
        controls.add_widget(reset_btn)
        controls.add_widget(diff_btn)
        root.add_widget(controls)

        # عرض Popup لاختيار الوضع
        Clock.schedule_once(lambda dt:self.choose_mode_popup(),0.2)

        return root

    # ------------------------ POPUPS ------------------------
    def choose_mode_popup(self):
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        popup = Popup(title="اختر الوضع", content=box, size_hint=(0.6,0.5), auto_dismiss=False)

        btn_2p = Button(text="2 Players", font_size=22)
        btn_ai = Button(text="Play vs AI", font_size=22)

        btn_2p.bind(on_release=lambda x:self.set_mode("2",popup))
        btn_ai.bind(on_release=lambda x:self.choose_ai_difficulty(popup))

        box.add_widget(btn_2p)
        box.add_widget(btn_ai)
        popup.open()

    def set_mode(self, mode, popup):
        self.mode = mode
        self.current = "X"
        self.msg_label.text=f"ابدأ! دور {self.current}"
        popup.dismiss()

    def choose_ai_difficulty(self, parent_popup=None):
        if parent_popup:
            parent_popup.dismiss()
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        popup = Popup(title="اختر مستوى AI", content=box, size_hint=(0.6,0.5), auto_dismiss=False)
        for lvl in ["Easy","Medium","Hard"]:
            btn = Button(text=lvl,font_size=22)
            btn.bind(on_release=lambda x,l=lvl:self.set_ai_mode(l,popup))
            box.add_widget(btn)
        popup.open()

    def set_ai_mode(self, level, popup):
        self.mode="ai"
        self.difficulty=level
        self.current=self.player
        self.msg_label.text=f"ابدأ! دور {self.current}"
        popup.dismiss()

    # ------------------------ GAME LOGIC ------------------------
    def cell_pressed(self, idx, btn):
        if self.game_over or self.current is None:
            return

        # مرحلة وضع القطع
        if self.phase == "place":
            if self.board[idx] != " ":
                return
            self.place_piece(idx, self.current)
            if self.check_winner(self.current):
                return
            self.switch_player()

        # مرحلة تحريك القطع
        else:
            # اختيار قطعة
            if self.selected_index is None:
                if self.board[idx] == self.current:
                    self.selected_index = idx
                    btn.background_color = (0.8,0.8,0.2,1)
                return
            # نقل القطعة
            if self.board[idx] == " ":
                from_idx = self.selected_index
                self.move_piece(from_idx, idx, self.current)
                self.selected_index=None
                if self.check_winner(self.current):
                    return
                self.switch_player()
            else:
                self.buttons[self.selected_index].background_color=(1,1,1,1)
                self.selected_index=None

    def place_piece(self, idx, player):
        self.board[idx] = player
        btn=self.buttons[idx]
        btn.text = player
        btn.color = (0,0,1,1) if player=="X" else (1,0,0,1)
        anim = Animation(font_size=80,duration=0.2)+Animation(font_size=48,duration=0.1)
        anim.start(btn)
        self.move_count[player]+=1
        if self.move_count["X"]==3 and self.move_count["O"]==3:
            self.phase="move"

    def move_piece(self, f, t, player):
        self.board[t]=player
        self.board[f]=" "
        btn_from = self.buttons[f]
        btn_to = self.buttons[t]
        btn_from.text=""
        btn_from.background_color=(1,1,1,1)
        btn_to.text=player
        btn_to.color = (0,0,1,1) if player=="X" else (1,0,0,1)
        anim = Animation(font_size=80,duration=0.2)+Animation(font_size=48,duration=0.1)
        anim.start(btn_to)

    def switch_player(self):
        if self.mode=="2":
            self.current="O" if self.current=="X" else "X"
            self.msg_label.text=f"دور اللاعب {self.current}"
        else:
            # AI Turn
            if self.current==self.player:
                self.current=self.ai
                self.msg_label.text="AI يفكر..."
                Clock.schedule_once(lambda dt:self.ai_turn(),0.3)
            else:
                self.current=self.player
                self.msg_label.text=f"دور اللاعب {self.current}"

    def check_winner(self, p):
        wins=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in wins:
            if self.board[a]==self.board[b]==self.board[c]==p:
                self.msg_label.text=f"الفائز: {p}"
                self.game_over=True
                self.score[p]+=1
                self.save_score()
                return True
        return False

    # ------------------------ AI ------------------------
    def ai_turn(self):
        if self.phase=="place":
            idx = self.ai_place()
            self.place_piece(idx,self.ai)
        else:
            from_idx,to_idx = self.ai_move()
            self.move_piece(from_idx,to_idx,self.ai)
        if self.check_winner(self.ai):
            return
        self.current=self.player
        self.msg_label.text=f"دور اللاعب {self.current}"

    def ai_place(self):
        empty = [i for i,v in enumerate(self.board) if v==" "]
        if self.difficulty=="Easy":
            return random.choice(empty)
        elif self.difficulty=="Medium":
            # منع اللاعب من الفوز أو كسب AI
            for i in empty:
                self.board[i]=self.ai
                if self.check_win(self.ai):
                    self.board[i]=" "
                    return i
                self.board[i]=" "
            for i in empty:
                self.board[i]=self.player
                if self.check_win(self.player):
                    self.board[i]=" "
                    return i
                self.board[i]=" "
            return random.choice(empty)
        else:
            # Hard - Minimax
            return self.minimax_root()

    def ai_move(self):
        ai_pieces=[i for i,v in enumerate(self.board) if v==self.ai]
        empty=[i for i,v in enumerate(self.board) if v==" "]
        for f in ai_pieces:
            for t in empty:
                self.board[f]=" "
                self.board[t]=self.ai
                if self.check_win(self.ai):
                    self.board[f]=self.ai
                    self.board[t]=" "
                    return f,t
                self.board[f]=self.ai
                self.board[t]=" "
        return random.choice(ai_pieces), random.choice(empty)

    def minimax_root(self):
        best_score=-999
        best_move=None
        for i,v in enumerate(self.board):
            if v==" ":
                self.board[i]=self.ai
                score=self.minimax(False)
                self.board[i]=" "
                if score>best_score:
                    best_score=score
                    best_move=i
        return best_move

    def minimax(self,is_max):
        if self.check_win(self.ai): return 10
        if self.check_win(self.player): return -10
        if all(v!=" " for v in self.board): return 0
        if is_max:
            best=-999
            for i,v in enumerate(self.board):
                if v==" ":
                    self.board[i]=self.ai
                    best=max(best,self.minimax(False))
                    self.board[i]=" "
            return best
        else:
            best=999
            for i,v in enumerate(self.board):
                if v==" ":
                    self.board[i]=self.player
                    best=min(best,self.minimax(True))
                    self.board[i]=" "
            return best

    # ------------------------ SCORE ------------------------
    def load_score(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE) as f:
                    parts=f.read().split(",")
                    self.score["X"]=int(parts[0])
                    self.score["O"]=int(parts[1])
            except:
                pass
        else:
            self.save_score()

    def save_score(self):
        with open(SCORE_FILE,"w") as f:
            f.write(f"{self.score['X']},{self.score['O']}")

    # ------------------------ RESET ------------------------
    def reset(self, *a):
        self.board=[" "]*9
        self.move_count={"X":0,"O":0}
        self.selected_index=None
        self.phase="place"
        self.game_over=False
        self.current=self.player
        self.msg_label.text=f"ابدأ! دور {self.current}"
        for b in self.buttons:
            b.text=""
            b.background_color=(1,1,1,1)

    # ------------------------ POPUP ------------------------
    def choose_level(self, *args):
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.level_popup = Popup(title="اختر مستوى AI", content=box, size_hint=(0.6,0.5), auto_dismiss=False)
        for lvl in ["Easy","Medium","Hard"]:
            btn=Button(text=lvl,font_size=22,background_normal='',background_color=(1,1,1,1),color=(0,0,0,1))
            btn.bind(on_release=lambda x,l=lvl:self.set_level(l))
            box.add_widget(btn)
        self.level_popup.open()

    def set_level(self, level):
        self.difficulty=level
        self.level_popup.dismiss()
        self.msg_label.text=f"اخترت: {level}"

    # ------------------------ UTILS ------------------------
    def check_win(self,p):
        w=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        return any(self.board[a]==self.board[b]==self.board[c]==p for a,b,c in w)

if __name__=="__main__":
    ThreeMensMorrisAI().run()
