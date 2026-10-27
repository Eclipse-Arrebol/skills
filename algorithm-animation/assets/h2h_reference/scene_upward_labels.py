"""Keep elimination-time incident weights visible while deriving H2H labels."""
from visual_base import *
from h2h_algorithm import label_terms

TP={"F":(4.3,3.2),"E":(4.3,1.6),"C":(4.3,0),
    "B":(2.6,-1.6),"D":(6.0,-1.6),"A":(2.6,-3.2)}


def dt(s,size=19,color=WHITE,width=2.79,t2c=None):
    obj=Text(s,font="Microsoft YaHei",font_size=size,color=color,
             disable_ligatures=True,t2c=t2c or {})
    if obj.width>width:
        obj.scale_to_fit_width(width)
    return obj


class PersistentTree:
    def __init__(self,scene):
        self.scene=scene
        self.nodes={}
        self.edges={}
        self.confirmed=set()
        self.sc={}
        self.labels={v:{} for v in VERTICES}
        self.active=set()
        self.sc_model={}
        self.label_changed={v:set() for v in VERTICES}

    def card(self,v,confirmed=True,saved=True):
        h=1.4 if v=="A" else 1.15
        rect=RoundedRectangle(width=3,height=h,corner_radius=.08,fill_color=BG,fill_opacity=1,
                              stroke_color=CYAN if confirmed else DIM,stroke_width=1.8)
        if not confirmed:
            rect=DashedVMobject(rect,num_dashes=28)
            content=VGroup(dt(v,25,DIM))
        else:
            head=dt(f"{v}: {{{','.join(MODEL['bags'][v])}}}",22).move_to([0,h/2-.2,0])
            pairs=list(self.sc.get(v,{}).items())
            sc_text="SC: —" if not saved else "SC: "+("  ".join(f"{u}:{w}" for u,w in pairs) or "∅")
            sc_colors={f"{u}:{w}":RED for u,w in pairs if MODEL["upward"][v].get(u)!=w}
            sc=dt(sc_text,19,CYAN,t2c=sc_colors).move_to([0,h/2-.55,0])
            rows=[]
            if v in self.active:
                targets=[a for a in MODEL["labels"][v] if a!=v] or [v]
                chunk=2 if v=="A" else 3
                for i in range(0,len(targets),chunk):
                    group=targets[i:i+chunk]
                    values={a:self.labels[v].get(a,"—") for a in group}
                    line=(f"L({v}): " if i==0 else "       ")+"  ".join(f"{a}:{values[a]}" for a in group)
                    colors={f"{a}:{values[a]}":RED for a in group if a in self.label_changed[v]}
                    rows.append(dt(line,19,YELLOW,t2c=colors).move_to([0,h/2-.9-.3*(i//chunk),0]))
            labs=VGroup(*rows)
            content=VGroup(head,sc,labs)
            for obj in content.family_members_with_points():
                assert obj.get_left()[0]>=-1.51 and obj.get_right()[0]<=1.51
                assert obj.get_top()[1]<=h/2+.01 and obj.get_bottom()[1]>=-h/2-.01
        return VGroup(rect,content).move_to(point(TP[v])).set_z_index(5)

    def insert(self,v,source):
        canonical=self.card(v,saved=False)
        target=canonical.copy()
        if v in self.nodes:
            flight=target.copy()
            self.scene.play(ReplacementTransform(self.nodes[v],target),TransformFromCopy(source,flight,path_arc=-.25),run_time=.5)
            self.scene.remove(flight)
        else:
            self.nodes[v]=target
            self.scene.play(TransformFromCopy(source,target,path_arc=-.25),run_time=.5)
        # Restore a pristine group after family alignment, and keep it as a
        # top-level scene object so newly added label rows are actually drawn.
        self.scene.remove(target)
        self.scene.add(canonical)
        self.nodes[v]=canonical
        self.confirmed.add(v)
        p=MODEL["parent"][v]
        if p:
            if p not in self.nodes:
                self.nodes[p]=self.card(p,False)
                self.scene.play(FadeIn(self.nodes[p]),run_time=.2)
            hv=1.4 if v=="A" else 1.15
            hp=1.4 if p=="A" else 1.15
            child=point(TP[v])+UP*hv/2
            parent=point(TP[p])+DOWN*hp/2
            line=Arrow(child,parent,buff=.025,
                       color=GREY,stroke_width=2.2,tip_length=.085).set_z_index(1)
            self.edges[v]=line
            self.scene.play(Create(line),run_time=.25)

    def save_sc(self,v,graph=None,model=MODEL):
        self.sc[v]=dict(model["upward"][v])
        self.sc_model[v]=model
        canonical=self.card(v)
        target=canonical.copy()
        if graph and self.sc[v]:
            weights=VGroup(*[graph.edges[edge(v,u)][1].copy() for u in self.sc[v]])
            flight=target[1][1].copy()
            self.scene.play(ReplacementTransform(self.nodes[v],target),TransformFromCopy(weights,flight),run_time=.5)
            self.scene.remove(flight)
        else:
            self.scene.play(ReplacementTransform(self.nodes[v],target),run_time=.4)
        self.scene.remove(target)
        self.scene.add(canonical)
        self.nodes[v]=canonical

    def set_label(self,v,a,value,updating=False):
        self.active.add(v)
        self.labels[v][a]=value
        if updating and MODEL["labels"][v][a]!=value:
            self.label_changed[v].add(a)
        canonical=self.card(v)
        target=canonical.copy()
        self.scene.play(ReplacementTransform(self.nodes[v],target),run_time=.26)
        self.scene.remove(target)
        self.scene.add(canonical)
        self.nodes[v]=canonical
        assert canonical in self.scene.mobjects

    def highlight(self,vs,color=YELLOW,t=.25):
        canonical={v:n.copy() for v,n in self.nodes.items()}
        for v,n in canonical.items():
            n[0].set_stroke(color if v in vs else CYAN,width=3 if v in vs else 1.8)
        targets={v:n.copy() for v,n in canonical.items()}
        self.scene.play(*[ReplacementTransform(self.nodes[v],targets[v]) for v in self.nodes],run_time=t)
        self.scene.remove(*targets.values())
        self.scene.add(*canonical.values())
        self.nodes=canonical

    def sc_row(self,v):
        return self.nodes[v][1][1]

    def label_rows(self,v):
        return self.nodes[v][1][2]


class H2HUpwardLabels(Scene):
    def construct(self):
        self.events=[]
        self.formula=None
        self.formulas=[]
        graph=BareGraph(self)
        tree=PersistentTree(self)
        def mark(name,**data):
            self.events.append(dict(name=name,time=float(self.time),**data))
        def derive(v,a,model=MODEL,updating=False,hold=.45):
            # SC is the frozen elimination-time incident map, never the list of
            # neighbor-pair fill candidates. All label sources must be visible.
            assert tree.sc[v]==model["upward"][v]
            reads=[]
            if a==v:
                value=0
                expression=f"L({v},{a}) = 0"
                terms={}
            else:
                pieces=[]
                terms={}
                for u,w in tree.sc[v].items():
                    if u==a:
                        d=0
                    else:
                        ref=(u,a) if a in model["labels"][u] else (a,u)
                        d=tree.labels[ref[0]][ref[1]]
                        assert d==model["labels"][ref[0]][ref[1]]
                        reads.append(ref)
                    pieces.append(f"{w}+{d}")
                    terms[u]=w+d
                value=min(terms.values())
                expression=f"L({v},{a}) = min("+", ".join(pieces)+f") = {value}"
                if len(pieces)==1:
                    expression=f"L({v},{a}) = {pieces[0]} = {value}"
                assert value==model["labels"][v][a]
            formula=dt(expression,25,YELLOW,width=7.3).move_to([-3.75,-3.85,0])
            anim=[Transform(self.formula,formula)] if self.formula is not None else [FadeIn(formula)]
            if self.formula is None:
                self.formula=formula
            anim.append(ShowPassingFlash(SurroundingRectangle(tree.sc_row(v),color=CYAN,buff=.025,stroke_width=1.6),time_width=.8))
            for source in dict.fromkeys(x for x,y in reads):
                anim.append(ShowPassingFlash(SurroundingRectangle(tree.label_rows(source),color=YELLOW,buff=.025,stroke_width=1.6),time_width=.8))
            self.play(*anim,run_time=.32)
            self.wait(.18)
            tree.set_label(v,a,value,updating)
            name=("update" if updating else "derive")+f"_{v}_{a}"
            mark(name,sc=dict(tree.sc[v]),reads=reads,terms=terms,value=value,formula=expression)
            self.formulas.append(dict(v=v,a=a,sc=dict(tree.sc[v]),reads=reads,terms=terms,value=value,
                                      formula=expression,updating=updating))
            self.wait(hold)
        mark("initial")
        self.wait(.7)
        for step in MODEL["steps"]:
            v=step["v"]
            graph.focus(v,step["neighbors"])
            self.wait(.15)
            for c in step["candidates"]:
                graph.candidate(v,c)
                self.wait(.12)
            tree.insert(v,graph.nodes[v])
            mark(f"bag_{v}",bag=step["bag"])
            tree.save_sc(v,graph)
            expected={u:step["before"][edge(v,u)] for u in step["neighbors"]}
            assert tree.sc[v]==expected
            mark(f"saved_SC_{v}",sc=dict(tree.sc[v]))
            self.wait(.65)
            graph.remove(v)
            self.wait(.15)
        mark("tree_complete")
        tree.highlight(VERTICES,GREEN)
        self.wait(.95)
        graph.restore()
        mark("labels_begin")
        for v in reversed(ORDER):
            tree.highlight([v])
            if v=="F":
                derive(v,v)
            else:
                for a in MODEL["labels"][v]:
                    if a!=v:
                        derive(v,a,hold=.65 if (v,a)==("A","E") else .4)
        mark("labels_complete")
        assert all(tree.sc[v]==MODEL["upward"][v] for v in VERTICES)
        self.wait(.8)
        self.play(FadeOut(self.formula),run_time=.2)
        self.formula=None
        tree.highlight(["C","E","F"])
        path=graph.path(["A","B","C","D"])
        self.play(Create(path),run_time=.4)
        mark("query_before")
        self.wait(1)
        self.play(FadeOut(path),run_time=.2)
        mark("dynamic_begin")
        tree.highlight([])
        graph.reveal_shortcuts()
        graph.change(("A","B"),9,RED)
        tree.save_sc("A",model=UPDATED)
        mark("SC_A_updated",sc=dict(tree.sc["A"]))
        self.wait(.65)
        graph.change(("B","F"),13,RED)
        tree.save_sc("B",model=UPDATED)
        mark("SC_B_updated",sc=dict(tree.sc["B"]))
        self.wait(.85)
        for k in [("C","F"),("E","F")]:
            self.play(Indicate(graph.edges[k][0],color=YELLOW,scale_factor=1),
                      Indicate(graph.edges[k][1][1],color=GREEN,scale_factor=1.04),run_time=.45)
            self.wait(.2)
        mark("shortcut_phase_done")
        # Saved SC has changed; all old L entries are still visible here.
        assert tree.labels["A"]["B"]==2 and tree.labels["B"]["F"]==6
        self.wait(.6)
        for v in ("B","A"):
            tree.highlight([v],RED)
            for a in UPDATED["labels"][v]:
                if a!=v:
                    derive(v,a,UPDATED,True,.5 if (v,a) in [("B","F"),("A","C")] else .3)
        mark("labels_phase_done")
        assert tree.labels["B"]["F"]==7 and tree.sc["B"]["F"]==13
        assert all(tree.labels[v][a]==d for v in VERTICES for a,d in UPDATED["labels"][v].items() if a!=v)
        self.play(FadeOut(self.formula),run_time=.2)
        tree.highlight(["C","E","F"])
        finalpath=graph.path(["A","F","E","D"],GREEN)
        self.play(Create(finalpath),run_time=.5)
        mark("query_after")
        self.wait(1.6)
        mark("end")
        (ROOT/"timeline.json").write_text(json.dumps(dict(duration=float(self.time),events=self.events,
                         formula_checks=self.formulas,SC_meaning="saved incident edges to remaining neighbors"),ensure_ascii=False,indent=2),encoding="utf-8")
