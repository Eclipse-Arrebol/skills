"""Presenter-led silent edition: graph and growing elimination tree only."""
import json
from pathlib import Path
import numpy as np
from manim import *
from graph_data import EDGES, ORDER, VERTICES, UPDATED_EDGES, edge
from h2h_algorithm import build, dynamic_update

ROOT = Path(__file__).resolve().parent
MODEL = build(EDGES)
UPDATED, SC_EVENTS, LABEL_EVENTS = dynamic_update(MODEL, UPDATED_EDGES)
BG = "#111827"
BLUE = "#619BEB"
CYAN = "#3FD9C8"
YELLOW = "#FFD35A"
RED = "#FF6978"
GREEN = "#72DDA2"
GREY = "#8999B1"
DIM = "#46546B"
WHITE = "#F2F5FA"
config.background_color = BG
config.frame_width = 16
config.frame_height = 9

GP = {"A":(-7.0,0), "B":(-5.25,2.65), "C":(-2.30,2.65),
      "D":(-.55,0), "E":(-2.30,-2.65), "F":(-5.25,-2.65)}
TP = {"F":(4.25,3), "E":(4.25,1.5), "C":(4.25,0),
      "B":(2.8,-1.5), "D":(5.75,-1.5), "A":(2.8,-3)}


def point(xy):
    return np.array([*xy, 0.0])


def text(s,size=32,color=WHITE):
    # Only graph vertices and numerical edge weights are permitted on canvas.
    assert str(s).isdigit() or str(s) in VERTICES
    return Text(str(s),font="Microsoft YaHei",font_size=size,color=color)


def node(v, position, color=BLUE, placeholder=False):
    circle=Circle(radius=.34,stroke_color=color,stroke_width=3,
                  fill_color=BG,fill_opacity=1)
    if placeholder:
        circle=DashedVMobject(circle,num_dashes=16)
    return VGroup(circle,text(v,34,DIM if placeholder else WHITE)).move_to(point(position)).set_z_index(5)


class BareGraph:
    def __init__(self, scene):
        self.scene=scene
        self.nodes={v:node(v,GP[v]) for v in VERTICES}
        self.edges={k:self.edge(k,w) for k,w in EDGES.items()}
        self.shortcut=set()
        self.values=dict(EDGES)
        self.scene.add(*self.edges.values(),*self.nodes.values())

    def edge(self,k,w,shortcut=False,color=None):
        p,q=(point(GP[v]) for v in k)
        c=color or (CYAN if shortcut else GREY)
        line=Line(p,q,buff=.36,color=c,stroke_width=2.5)
        if shortcut:
            line=DashedLine(line.get_start(),line.get_end(),color=c,dash_length=.12,stroke_width=3.1)
        offset={("A","B"):(-.25,.02),("B","C"):(0,.25),
                ("C","D"):(.25,.02),("D","E"):(.25,-.02),
                ("E","F"):(0,-.25),("A","F"):(-.25,-.02),
                ("B","E"):(-.38,.87),("C","F"):(-.5,-.87),
                ("B","F"):(-.29,0),("C","E"):(.29,0)}[k]
        number=text(w,29,c).move_to((p+q)/2+[*offset,0])
        back=BackgroundRectangle(number,color=BG,fill_opacity=1,buff=.05,stroke_width=0)
        return VGroup(line,VGroup(back,number).set_z_index(3))

    def focus(self,v,ns):
        self.scene.play(*[obj[0].animate.set_stroke(YELLOW if u==v else CYAN if u in ns else BLUE,
                                                  width=4.5 if u==v else 3) for u,obj in self.nodes.items()],run_time=.36)

    def candidate(self,v,c):
        k=edge(c["x"],c["y"])
        self.scene.play(*[Indicate(self.edges[edge(v,u)][0],color=YELLOW,scale_factor=1)
                          for u in (c["x"],c["y"])],run_time=.42)
        if c["action"]=="add":
            self.shortcut.add(k)
            self.values[k]=c["value"]
            self.edges[k]=self.edge(k,c["value"],True)
            self.scene.play(Create(self.edges[k][0]),FadeIn(self.edges[k][1]),run_time=.5)
        elif c["action"]=="update":
            self.change(k,c["value"],CYAN)
        else:
            self.scene.play(Indicate(self.edges[k],color=CYAN,scale_factor=1),run_time=.35)

    def remove(self,v):
        incident=[k for k in self.edges if v in k]
        self.scene.play(FadeOut(self.nodes[v],scale=.25),*[FadeOut(self.edges[k]) for k in incident],run_time=.5)
        del self.nodes[v]
        for k in incident:
            del self.edges[k]
        if self.nodes:
            self.scene.play(*[n[0].animate.set_stroke(BLUE,width=3) for n in self.nodes.values()],run_time=.2)

    def change(self,k,value,color):
        self.scene.play(Transform(self.edges[k],self.edge(k,value,k in self.shortcut,color)),run_time=.65)
        self.values[k]=value

    def path(self,vertices,color=YELLOW):
        return VGroup(*[self.edges[edge(u,v)][0].copy().set_stroke(color,width=6)
                        for u,v in zip(vertices,vertices[1:])]).set_z_index(2)

    def restore(self):
        nodes={v:node(v,GP[v]) for v in VERTICES}
        edges={k:self.edge(k,w) for k,w in EDGES.items()}
        self.nodes,self.edges,self.values,self.shortcut=nodes,edges,dict(EDGES),set()
        self.scene.play(*[FadeIn(obj) for obj in edges.values()],*[FadeIn(obj) for obj in nodes.values()],run_time=.7)

    def reveal_shortcuts(self):
        for k in [("B","F"),("C","E")]:
            self.shortcut.add(k)
            self.values[k]=MODEL["weights"][k]
            self.edges[k]=self.edge(k,self.values[k],True)
        self.scene.play(*[Create(self.edges[k][0]) for k in self.shortcut],
                        *[FadeIn(self.edges[k][1]) for k in self.shortcut],run_time=.55)
