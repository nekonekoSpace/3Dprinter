



import FreeCAD as App
import Part
from FreeCAD import Vector, Rotation, Placement



def create_oden(doc_name="Main"):
    """おでんの3Dモデルを作成する関数"""


    ### Begin command PartDesign_Body
    App.activeDocument().addObject('PartDesign::Body','Body')
    App.ActiveDocument.getObject('Body').Label = 'Body'
    # Gui.activateView('Gui::View3DInventor', True)
    # Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection(App.ActiveDocument.Body)
    App.ActiveDocument.recompute()
    ### End command PartDesign_Body
    # Gui.Selection.addSelection('Main','Body')
    # Gui.runCommand('PartDesign_NewSketch',0)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body','Origin.XZ_Plane.')
    App.getDocument('Main').getObject('Body').newObject('Sketcher::SketchObject','Sketch')
    App.getDocument('Main').getObject('Sketch').AttachmentSupport = (App.getDocument('Main').getObject('XZ_Plane'),[''])
    App.getDocument('Main').getObject('Sketch').MapMode = 'FlatFace'
    App.ActiveDocument.recompute()
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body'), 0, 'Sketch.')
    # ActiveSketch = App.getDocument('Main').getObject('Sketch')
    # tv = Show.TempoVis(App.ActiveDocument, tag= ActiveSketch.ViewObject.TypeId)
    # ActiveSketch.ViewObject.TempoVis = tv
    # if ActiveSketch.ViewObject.EditingWorkbench:
    #   tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
    # if ActiveSketch.ViewObject.HideDependent:
    #   tv.hide(tv.get_all_dependent(App.getDocument('Main').getObject('Body'), 'Sketch.'))
    # if ActiveSketch.ViewObject.ShowSupport:
    #   tv.show([ref[0] for ref in ActiveSketch.AttachmentSupport if not ref[0].isDerivedFrom("PartDesign::Plane")])
    # if ActiveSketch.ViewObject.ShowLinks:
    #   tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
    # tv.sketchClipPlane(ActiveSketch, ActiveSketch.ViewObject.SectionView)
    # tv.hide(ActiveSketch)
    # del(tv)
    # del(ActiveSketch)
    # 
    import PartDesignGui
    # ActiveSketch = App.getDocument('Main').getObject('Sketch')
    # if ActiveSketch.ViewObject.RestoreCamera:
    #   ActiveSketch.ViewObject.TempoVis.saveCamera()
    #   if ActiveSketch.ViewObject.ForceOrtho:
    #     ActiveSketch.ViewObject.Document.ActiveView.setCameraType('Orthographic')
    # 
    # Gui.Selection.clearSelection()
    # Gui.runCommand('Sketcher_CompCreateConic',0)
    ActiveSketch = App.getDocument('Main').getObject('Sketch')

    lastGeoId = len(ActiveSketch.Geometry)

    geoList = []
    geoList.append(Part.Circle(App.Vector(0.000000, 0.000000, 0.000000), App.Vector(0.000000, 0.000000, 1.000000), 40.000000))
    App.getDocument('Main').getObject('Sketch').addGeometry(geoList,False)
    del geoList

    constraintList = []
    App.getDocument('Main').getObject('Sketch').addConstraint(Sketcher.Constraint('Diameter',0,80.000000)) 
    App.getDocument('Main').getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))


    App.ActiveDocument.recompute()
    # Gui.getDocument('Main').resetEdit()
    App.ActiveDocument.recompute()
    # ActiveSketch = App.getDocument('Main').getObject('Sketch')
    # tv = ActiveSketch.ViewObject.TempoVis
    # if tv:
    #   tv.restore()
    # ActiveSketch.ViewObject.TempoVis = None
    # del(tv)
    # del(ActiveSketch)
    # 
    # Gui.Selection.addSelection('Main','Body','Sketch.')
    App.getDocument('Main').recompute()
    ### Begin command PartDesign_Pad
    App.getDocument('Main').getObject('Body').newObject('PartDesign::Pad','Pad')
    App.getDocument('Main').getObject('Pad').Profile = (App.getDocument('Main').getObject('Sketch'), ['',])
    App.getDocument('Main').getObject('Pad').Length = 10
    App.ActiveDocument.recompute()
    App.getDocument('Main').getObject('Pad').ReferenceAxis = (App.getDocument('Main').getObject('Sketch'),['N_Axis'])
    App.getDocument('Main').getObject('Sketch').Visibility = False
    App.ActiveDocument.recompute()
    # App.getDocument('Main').getObject('Pad').ViewObject.ShapeAppearance=getattr(App.getDocument('Main').getObject('Body').getLinkedObject(True).ViewObject,'ShapeAppearance',App.getDocument('Main').getObject('Pad').ViewObject.ShapeAppearance)
    # App.getDocument('Main').getObject('Pad').ViewObject.LineColor=getattr(App.getDocument('Main').getObject('Body').getLinkedObject(True).ViewObject,'LineColor',App.getDocument('Main').getObject('Pad').ViewObject.LineColor)
    # App.getDocument('Main').getObject('Pad').ViewObject.PointColor=getattr(App.getDocument('Main').getObject('Body').getLinkedObject(True).ViewObject,'PointColor',App.getDocument('Main').getObject('Pad').ViewObject.PointColor)
    # App.getDocument('Main').getObject('Pad').ViewObject.Transparency=getattr(App.getDocument('Main').getObject('Body').getLinkedObject(True).ViewObject,'Transparency',App.getDocument('Main').getObject('Pad').ViewObject.Transparency)
    # App.getDocument('Main').getObject('Pad').ViewObject.DisplayMode=getattr(App.getDocument('Main').getObject('Body').getLinkedObject(True).ViewObject,'DisplayMode',App.getDocument('Main').getObject('Pad').ViewObject.DisplayMode)
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body'), 0, 'Pad.')
    # Gui.Selection.clearSelection()
    ### End command PartDesign_Pad
    # Gui.Selection.clearSelection()
    App.getDocument('Main').getObject('Pad').Length = 20.000000
    App.getDocument('Main').getObject('Pad').TaperAngle = 0.000000
    App.getDocument('Main').getObject('Pad').UseCustomVector = 0
    App.getDocument('Main').getObject('Pad').Direction = (0, -1, 0)
    App.getDocument('Main').getObject('Pad').ReferenceAxis = (App.getDocument('Main').getObject('Sketch'), ['N_Axis'])
    App.getDocument('Main').getObject('Pad').AlongSketchNormal = 1
    App.getDocument('Main').getObject('Pad').Type = 0
    App.getDocument('Main').getObject('Pad').UpToFace = None
    App.getDocument('Main').getObject('Pad').Reversed = 0
    App.getDocument('Main').getObject('Pad').Midplane = 1
    App.getDocument('Main').getObject('Pad').Offset = 0
    App.getDocument('Main').recompute()
    # Gui.getDocument('Main').resetEdit()
    App.getDocument('Main').getObject('Sketch').Visibility = False














    ### Begin command PartDesign_Body
    App.activeDocument().addObject('PartDesign::Body','Body001')
    App.ActiveDocument.getObject('Body001').Label = 'Body'
    # Gui.activateView('Gui::View3DInventor', True)
    # Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body001)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection(App.ActiveDocument.Body001)
    App.ActiveDocument.recompute()
    ### End command PartDesign_Body
    # Gui.Selection.addSelection('Main','Body001')
    # Gui.runCommand('PartDesign_NewSketch',0)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body001','Origin001.XZ_Plane001.')
    App.getDocument('Main').getObject('Body001').newObject('Sketcher::SketchObject','Sketch001')
    App.getDocument('Main').getObject('Sketch001').AttachmentSupport = (App.getDocument('Main').getObject('XZ_Plane001'),[''])
    App.getDocument('Main').getObject('Sketch001').MapMode = 'FlatFace'
    App.ActiveDocument.recompute()
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body001'), 0, 'Sketch001.')
    # ActiveSketch = App.getDocument('Main').getObject('Sketch001')
    # tv = Show.TempoVis(App.ActiveDocument, tag= ActiveSketch.ViewObject.TypeId)
    # ActiveSketch.ViewObject.TempoVis = tv
    # if ActiveSketch.ViewObject.EditingWorkbench:
    #   tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
    # if ActiveSketch.ViewObject.HideDependent:
    #   tv.hide(tv.get_all_dependent(App.getDocument('Main').getObject('Body001'), 'Sketch001.'))
    # if ActiveSketch.ViewObject.ShowSupport:
    #   tv.show([ref[0] for ref in ActiveSketch.AttachmentSupport if not ref[0].isDerivedFrom("PartDesign::Plane")])
    # if ActiveSketch.ViewObject.ShowLinks:
    #   tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
    # tv.sketchClipPlane(ActiveSketch, ActiveSketch.ViewObject.SectionView)
    # tv.hide(ActiveSketch)
    # del(tv)
    # del(ActiveSketch)
    # 
    import PartDesignGui
    # ActiveSketch = App.getDocument('Main').getObject('Sketch001')
    # if ActiveSketch.ViewObject.RestoreCamera:
    #   ActiveSketch.ViewObject.TempoVis.saveCamera()
    #   if ActiveSketch.ViewObject.ForceOrtho:
    #     ActiveSketch.ViewObject.Document.ActiveView.setCameraType('Orthographic')
    # 
    # Gui.Selection.clearSelection()
    # Gui.runCommand('Sketcher_CompCreateRectangles',1)
    ActiveSketch = App.getDocument('Main').getObject('Sketch001')

    lastGeoId = len(ActiveSketch.Geometry)

    geoList = []
    geoList.append(Part.LineSegment(App.Vector(-60.000000, -100.545181, 0.000000),App.Vector(60.000000, -100.545181, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(60.000000, -100.545181, 0.000000),App.Vector(60.000000, -60.545181, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(60.000000, -60.545181, 0.000000),App.Vector(-60.000000, -60.545181, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(-60.000000, -60.545181, 0.000000),App.Vector(-60.000000, -100.545181, 0.000000)))
    App.getDocument('Main').getObject('Sketch001').addGeometry(geoList,False)
    del geoList

    constrGeoList = []
    constrGeoList.append(Part.Point(App.Vector(0.000000, -80.545181, 0.000000)))
    App.getDocument('Main').getObject('Sketch001').addGeometry(constrGeoList,True)
    del constrGeoList

    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 2, 2, 3, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 3, 2, 0, 1))
    constraintList.append(Sketcher.Constraint('Horizontal', 0))
    constraintList.append(Sketcher.Constraint('Horizontal', 2))
    constraintList.append(Sketcher.Constraint('Vertical', 1))
    constraintList.append(Sketcher.Constraint('Vertical', 3))
    constraintList.append(Sketcher.Constraint('Symmetric', 2, 1, 0, 1, 4, 1))
    App.getDocument('Main').getObject('Sketch001').addConstraint(constraintList)
    del constraintList

    App.getDocument('Main').getObject('Sketch001').addConstraint(Sketcher.Constraint('Distance',1,1,3,2,120.000000)) 
    App.getDocument('Main').getObject('Sketch001').addConstraint(Sketcher.Constraint('Distance',0,1,2,2,40.000000)) 
    App.getDocument('Main').getObject('Sketch001').addConstraint(Sketcher.Constraint('PointOnObject', 4, 1, -2))


    App.ActiveDocument.recompute()
    # Gui.runCommand('Sketcher_CompDimensionTools',0)
    App.getDocument('Main').getObject('Sketch001').addConstraint(Sketcher.Constraint('Distance',4,1,-1,1,80.545181)) 
    # Gui.Selection.addSelection('Main','Body001','Sketch001.Vertex9',0,-80.5452,0)
    # App.getDocument('Main').getObject('Sketch001').addConstraint(Sketcher.Constraint('DistanceY',4,1,-1,1,80.545181)) 
    App.getDocument('Main').getObject('Sketch001').setDatum(12,App.Units.Quantity('70.000000 mm'))
    App.ActiveDocument.recompute()
    # Gui.Selection.clearSelection()
    # Gui.getDocument('Main').resetEdit()
    App.ActiveDocument.recompute()
    # ActiveSketch = App.getDocument('Main').getObject('Sketch001')
    # tv = ActiveSketch.ViewObject.TempoVis
    # if tv:
    #   tv.restore()
    # ActiveSketch.ViewObject.TempoVis = None
    # del(tv)
    # del(ActiveSketch)
    # 
    # Gui.Selection.addSelection('Main','Body001','Sketch001.')
    App.getDocument('Main').recompute()
    ### Begin command PartDesign_Pad
    App.getDocument('Main').getObject('Body001').newObject('PartDesign::Pad','Pad001')
    App.getDocument('Main').getObject('Pad001').Profile = (App.getDocument('Main').getObject('Sketch001'), ['',])
    App.getDocument('Main').getObject('Pad001').Length = 10
    App.ActiveDocument.recompute()
    App.getDocument('Main').getObject('Pad001').ReferenceAxis = (App.getDocument('Main').getObject('Sketch001'),['N_Axis'])
    App.getDocument('Main').getObject('Sketch001').Visibility = False
    App.ActiveDocument.recompute()
    # App.getDocument('Main').getObject('Pad001').ViewObject.ShapeAppearance=getattr(App.getDocument('Main').getObject('Body001').getLinkedObject(True).ViewObject,'ShapeAppearance',App.getDocument('Main').getObject('Pad001').ViewObject.ShapeAppearance)
    # App.getDocument('Main').getObject('Pad001').ViewObject.LineColor=getattr(App.getDocument('Main').getObject('Body001').getLinkedObject(True).ViewObject,'LineColor',App.getDocument('Main').getObject('Pad001').ViewObject.LineColor)
    # App.getDocument('Main').getObject('Pad001').ViewObject.PointColor=getattr(App.getDocument('Main').getObject('Body001').getLinkedObject(True).ViewObject,'PointColor',App.getDocument('Main').getObject('Pad001').ViewObject.PointColor)
    # App.getDocument('Main').getObject('Pad001').ViewObject.Transparency=getattr(App.getDocument('Main').getObject('Body001').getLinkedObject(True).ViewObject,'Transparency',App.getDocument('Main').getObject('Pad001').ViewObject.Transparency)
    # App.getDocument('Main').getObject('Pad001').ViewObject.DisplayMode=getattr(App.getDocument('Main').getObject('Body001').getLinkedObject(True).ViewObject,'DisplayMode',App.getDocument('Main').getObject('Pad001').ViewObject.DisplayMode)
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body001'), 0, 'Pad001.')
    # Gui.Selection.clearSelection()
    ### End command PartDesign_Pad
    # Gui.Selection.clearSelection()
    App.getDocument('Main').getObject('Pad001').Length = 20.000000
    App.getDocument('Main').getObject('Pad001').TaperAngle = 0.000000
    App.getDocument('Main').getObject('Pad001').UseCustomVector = 0
    App.getDocument('Main').getObject('Pad001').Direction = (0, -1, 0)
    App.getDocument('Main').getObject('Pad001').ReferenceAxis = (App.getDocument('Main').getObject('Sketch001'), ['N_Axis'])
    App.getDocument('Main').getObject('Pad001').AlongSketchNormal = 1
    App.getDocument('Main').getObject('Pad001').Type = 0
    App.getDocument('Main').getObject('Pad001').UpToFace = None
    App.getDocument('Main').getObject('Pad001').Reversed = 0
    App.getDocument('Main').getObject('Pad001').Midplane = 1
    App.getDocument('Main').getObject('Pad001').Offset = 0
    App.getDocument('Main').recompute()
    # Gui.getDocument('Main').resetEdit()
    App.getDocument('Main').getObject('Sketch001').Visibility = False
















    ### Begin command PartDesign_Body
    App.activeDocument().addObject('PartDesign::Body','Body002')
    App.ActiveDocument.getObject('Body002').Label = 'Body'
    # Gui.activateView('Gui::View3DInventor', True)
    # Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body002)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection(App.ActiveDocument.Body002)
    App.ActiveDocument.recompute()
    ### End command PartDesign_Body
    # Gui.Selection.addSelection('Main','Body002')
    # Gui.runCommand('PartDesign_NewSketch',0)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body002','Origin002.XZ_Plane002.')
    App.getDocument('Main').getObject('Body002').newObject('Sketcher::SketchObject','Sketch002')
    App.getDocument('Main').getObject('Sketch002').AttachmentSupport = (App.getDocument('Main').getObject('XZ_Plane002'),[''])
    App.getDocument('Main').getObject('Sketch002').MapMode = 'FlatFace'
    App.ActiveDocument.recompute()
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body002'), 0, 'Sketch002.')
    # ActiveSketch = App.getDocument('Main').getObject('Sketch002')
    # tv = Show.TempoVis(App.ActiveDocument, tag= ActiveSketch.ViewObject.TypeId)
    # ActiveSketch.ViewObject.TempoVis = tv
    # if ActiveSketch.ViewObject.EditingWorkbench:
    #   tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
    # if ActiveSketch.ViewObject.HideDependent:
    #   tv.hide(tv.get_all_dependent(App.getDocument('Main').getObject('Body002'), 'Sketch002.'))
    # if ActiveSketch.ViewObject.ShowSupport:
    #   tv.show([ref[0] for ref in ActiveSketch.AttachmentSupport if not ref[0].isDerivedFrom("PartDesign::Plane")])
    # if ActiveSketch.ViewObject.ShowLinks:
    #   tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
    # tv.sketchClipPlane(ActiveSketch, ActiveSketch.ViewObject.SectionView)
    # tv.hide(ActiveSketch)
    # del(tv)
    # del(ActiveSketch)
    # 
    import PartDesignGui
    # ActiveSketch = App.getDocument('Main').getObject('Sketch002')
    # if ActiveSketch.ViewObject.RestoreCamera:
    #   ActiveSketch.ViewObject.TempoVis.saveCamera()
    #   if ActiveSketch.ViewObject.ForceOrtho:
    #     ActiveSketch.ViewObject.Document.ActiveView.setCameraType('Orthographic')
    # 
    # Gui.Selection.clearSelection()
    # Gui.runCommand('Sketcher_CompCreateRectangles',1)
    ActiveSketch = App.getDocument('Main').getObject('Sketch002')

    lastGeoId = len(ActiveSketch.Geometry)

    geoList = []
    geoList.append(Part.LineSegment(App.Vector(-15.000000, 71.286987, 0.000000),App.Vector(15.000000, 71.286987, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(15.000000, 71.286987, 0.000000),App.Vector(15.000000, 101.286987, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(15.000000, 101.286987, 0.000000),App.Vector(-15.000000, 101.286987, 0.000000)))
    geoList.append(Part.LineSegment(App.Vector(-15.000000, 101.286987, 0.000000),App.Vector(-15.000000, 71.286987, 0.000000)))
    App.getDocument('Main').getObject('Sketch002').addGeometry(geoList,False)
    del geoList

    constrGeoList = []
    constrGeoList.append(Part.Point(App.Vector(0.000000, 86.286987, 0.000000)))
    App.getDocument('Main').getObject('Sketch002').addGeometry(constrGeoList,True)
    del constrGeoList

    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 2, 2, 3, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 3, 2, 0, 1))
    constraintList.append(Sketcher.Constraint('Horizontal', 0))
    constraintList.append(Sketcher.Constraint('Horizontal', 2))
    constraintList.append(Sketcher.Constraint('Vertical', 1))
    constraintList.append(Sketcher.Constraint('Vertical', 3))
    constraintList.append(Sketcher.Constraint('Symmetric', 2, 1, 0, 1, 4, 1))
    App.getDocument('Main').getObject('Sketch002').addConstraint(constraintList)
    del constraintList

    App.getDocument('Main').getObject('Sketch002').addConstraint(Sketcher.Constraint('Distance',1,1,3,2,80.000000)) 
    App.getDocument('Main').getObject('Sketch002').addConstraint(Sketcher.Constraint('Distance',0,1,2,2,80.000000)) 
    App.getDocument('Main').getObject('Sketch002').addConstraint(Sketcher.Constraint('PointOnObject', 4, 1, -2))


    App.ActiveDocument.recompute()
    # Gui.runCommand('Sketcher_CompDimensionTools',0)
    App.getDocument('Main').getObject('Sketch002').addConstraint(Sketcher.Constraint('Distance',4,1,-1,1,86.286987)) 
    # Gui.Selection.addSelection('Main','Body002','Sketch002.Vertex9',0,86.287,0)
    # App.getDocument('Main').getObject('Sketch002').addConstraint(Sketcher.Constraint('DistanceY',-1,1,4,1,86.286987)) 
    App.getDocument('Main').getObject('Sketch002').setDatum(12,App.Units.Quantity('90.000000 mm'))
    App.ActiveDocument.recompute()
    # Gui.Selection.clearSelection()
    # Gui.getDocument('Main').resetEdit()
    App.ActiveDocument.recompute()
    # ActiveSketch = App.getDocument('Main').getObject('Sketch002')
    # tv = ActiveSketch.ViewObject.TempoVis
    # if tv:
    #   tv.restore()
    # ActiveSketch.ViewObject.TempoVis = None
    # del(tv)
    # del(ActiveSketch)
    # 
    # Gui.Selection.addSelection('Main','Body002','Sketch002.')
    App.getDocument('Main').recompute()
    ### Begin command PartDesign_Pad
    App.getDocument('Main').getObject('Body002').newObject('PartDesign::Pad','Pad002')
    App.getDocument('Main').getObject('Pad002').Profile = (App.getDocument('Main').getObject('Sketch002'), ['',])
    App.getDocument('Main').getObject('Pad002').Length = 10
    App.ActiveDocument.recompute()
    App.getDocument('Main').getObject('Pad002').ReferenceAxis = (App.getDocument('Main').getObject('Sketch002'),['N_Axis'])
    App.getDocument('Main').getObject('Sketch002').Visibility = False
    App.ActiveDocument.recompute()
    # App.getDocument('Main').getObject('Pad002').ViewObject.ShapeAppearance=getattr(App.getDocument('Main').getObject('Body002').getLinkedObject(True).ViewObject,'ShapeAppearance',App.getDocument('Main').getObject('Pad002').ViewObject.ShapeAppearance)
    # App.getDocument('Main').getObject('Pad002').ViewObject.LineColor=getattr(App.getDocument('Main').getObject('Body002').getLinkedObject(True).ViewObject,'LineColor',App.getDocument('Main').getObject('Pad002').ViewObject.LineColor)
    # App.getDocument('Main').getObject('Pad002').ViewObject.PointColor=getattr(App.getDocument('Main').getObject('Body002').getLinkedObject(True).ViewObject,'PointColor',App.getDocument('Main').getObject('Pad002').ViewObject.PointColor)
    # App.getDocument('Main').getObject('Pad002').ViewObject.Transparency=getattr(App.getDocument('Main').getObject('Body002').getLinkedObject(True).ViewObject,'Transparency',App.getDocument('Main').getObject('Pad002').ViewObject.Transparency)
    # App.getDocument('Main').getObject('Pad002').ViewObject.DisplayMode=getattr(App.getDocument('Main').getObject('Body002').getLinkedObject(True).ViewObject,'DisplayMode',App.getDocument('Main').getObject('Pad002').ViewObject.DisplayMode)
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body002'), 0, 'Pad002.')
    # Gui.Selection.clearSelection()
    ### End command PartDesign_Pad
    # Gui.Selection.clearSelection()
    App.getDocument('Main').getObject('Pad002').Length = 20.000000
    App.getDocument('Main').getObject('Pad002').TaperAngle = 0.000000
    App.getDocument('Main').getObject('Pad002').UseCustomVector = 0
    App.getDocument('Main').getObject('Pad002').Direction = (0, -1, 0)
    App.getDocument('Main').getObject('Pad002').ReferenceAxis = (App.getDocument('Main').getObject('Sketch002'), ['N_Axis'])
    App.getDocument('Main').getObject('Pad002').AlongSketchNormal = 1
    App.getDocument('Main').getObject('Pad002').Type = 0
    App.getDocument('Main').getObject('Pad002').UpToFace = None
    App.getDocument('Main').getObject('Pad002').Reversed = 0
    App.getDocument('Main').getObject('Pad002').Midplane = 1
    App.getDocument('Main').getObject('Pad002').Offset = 0
    App.getDocument('Main').recompute()
    # Gui.getDocument('Main').resetEdit()
    App.getDocument('Main').getObject('Sketch002').Visibility = False








    ### Begin command PartDesign_Body
    App.activeDocument().addObject('PartDesign::Body','Body003')
    App.ActiveDocument.getObject('Body003').Label = 'Body'
    # Gui.activateView('Gui::View3DInventor', True)
    # Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body003)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection(App.ActiveDocument.Body003)
    App.ActiveDocument.recompute()
    ### End command PartDesign_Body
    # Gui.Selection.addSelection('Main','Body003')
    # Gui.runCommand('PartDesign_NewSketch',0)
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body003','Origin003.XY_Plane003.')
    App.getDocument('Main').getObject('Body003').newObject('Sketcher::SketchObject','Sketch003')
    App.getDocument('Main').getObject('Sketch003').AttachmentSupport = (App.getDocument('Main').getObject('XY_Plane003'),[''])
    App.getDocument('Main').getObject('Sketch003').MapMode = 'FlatFace'
    App.ActiveDocument.recompute()
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body003'), 0, 'Sketch003.')
    # ActiveSketch = App.getDocument('Main').getObject('Sketch003')
    # tv = Show.TempoVis(App.ActiveDocument, tag= ActiveSketch.ViewObject.TypeId)
    # ActiveSketch.ViewObject.TempoVis = tv
    # if ActiveSketch.ViewObject.EditingWorkbench:
    #   tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
    # if ActiveSketch.ViewObject.HideDependent:
    #   tv.hide(tv.get_all_dependent(App.getDocument('Main').getObject('Body003'), 'Sketch003.'))
    # if ActiveSketch.ViewObject.ShowSupport:
    #   tv.show([ref[0] for ref in ActiveSketch.AttachmentSupport if not ref[0].isDerivedFrom("PartDesign::Plane")])
    # if ActiveSketch.ViewObject.ShowLinks:
    #   tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
    # tv.sketchClipPlane(ActiveSketch, ActiveSketch.ViewObject.SectionView)
    # tv.hide(ActiveSketch)
    # del(tv)
    # del(ActiveSketch)
    # 
    import PartDesignGui
    # ActiveSketch = App.getDocument('Main').getObject('Sketch003')
    # if ActiveSketch.ViewObject.RestoreCamera:
    #   ActiveSketch.ViewObject.TempoVis.saveCamera()
    #   if ActiveSketch.ViewObject.ForceOrtho:
    #     ActiveSketch.ViewObject.Document.ActiveView.setCameraType('Orthographic')
    # 
    # Gui.Selection.clearSelection()
    # Gui.runCommand('Sketcher_CompCreateConic',0)
    # Gui.Selection.addSelection('Main','Body003')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body002')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body001')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body')
    ActiveSketch = App.getDocument('Main').getObject('Sketch003')

    lastGeoId = len(ActiveSketch.Geometry)

    geoList = []
    geoList.append(Part.Circle(App.Vector(0.000000, 0.000000, 0.000000), App.Vector(0.000000, 0.000000, 1.000000), 5.000000))
    App.getDocument('Main').getObject('Sketch003').addGeometry(geoList,False)
    del geoList

    constraintList = []
    App.getDocument('Main').getObject('Sketch003').addConstraint(Sketcher.Constraint('Diameter',0,10.000000)) 
    App.getDocument('Main').getObject('Sketch003').addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))


    App.ActiveDocument.recompute()
    # Gui.Selection.clearSelection()
    # Gui.getDocument('Main').resetEdit()
    App.ActiveDocument.recompute()
    # ActiveSketch = App.getDocument('Main').getObject('Sketch003')
    # tv = ActiveSketch.ViewObject.TempoVis
    # if tv:
    #   tv.restore()
    # ActiveSketch.ViewObject.TempoVis = None
    # del(tv)
    # del(ActiveSketch)
    # 
    # Gui.Selection.addSelection('Main','Body003','Sketch003.')
    App.getDocument('Main').recompute()
    ### Begin command PartDesign_Pad
    App.getDocument('Main').getObject('Body003').newObject('PartDesign::Pad','Pad003')
    App.getDocument('Main').getObject('Pad003').Profile = (App.getDocument('Main').getObject('Sketch003'), ['',])
    App.getDocument('Main').getObject('Pad003').Length = 10
    App.ActiveDocument.recompute()
    App.getDocument('Main').getObject('Pad003').ReferenceAxis = (App.getDocument('Main').getObject('Sketch003'),['N_Axis'])
    App.getDocument('Main').getObject('Sketch003').Visibility = False
    App.ActiveDocument.recompute()
    # App.getDocument('Main').getObject('Pad003').ViewObject.ShapeAppearance=getattr(App.getDocument('Main').getObject('Body003').getLinkedObject(True).ViewObject,'ShapeAppearance',App.getDocument('Main').getObject('Pad003').ViewObject.ShapeAppearance)
    # App.getDocument('Main').getObject('Pad003').ViewObject.LineColor=getattr(App.getDocument('Main').getObject('Body003').getLinkedObject(True).ViewObject,'LineColor',App.getDocument('Main').getObject('Pad003').ViewObject.LineColor)
    # App.getDocument('Main').getObject('Pad003').ViewObject.PointColor=getattr(App.getDocument('Main').getObject('Body003').getLinkedObject(True).ViewObject,'PointColor',App.getDocument('Main').getObject('Pad003').ViewObject.PointColor)
    # App.getDocument('Main').getObject('Pad003').ViewObject.Transparency=getattr(App.getDocument('Main').getObject('Body003').getLinkedObject(True).ViewObject,'Transparency',App.getDocument('Main').getObject('Pad003').ViewObject.Transparency)
    # App.getDocument('Main').getObject('Pad003').ViewObject.DisplayMode=getattr(App.getDocument('Main').getObject('Body003').getLinkedObject(True).ViewObject,'DisplayMode',App.getDocument('Main').getObject('Pad003').ViewObject.DisplayMode)
    # Gui.getDocument('Main').setEdit(App.getDocument('Main').getObject('Body003'), 0, 'Pad003.')
    # Gui.Selection.clearSelection()
    ### End command PartDesign_Pad
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body003')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body002')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body001')
    # Gui.Selection.clearSelection()
    # Gui.Selection.addSelection('Main','Body')
    App.getDocument('Main').getObject('Pad003').Length = 300.000000
    App.getDocument('Main').getObject('Pad003').TaperAngle = 0.000000
    App.getDocument('Main').getObject('Pad003').UseCustomVector = 0
    App.getDocument('Main').getObject('Pad003').Direction = (0, 0, 1)
    App.getDocument('Main').getObject('Pad003').ReferenceAxis = (App.getDocument('Main').getObject('Sketch003'), ['N_Axis'])
    App.getDocument('Main').getObject('Pad003').AlongSketchNormal = 1
    App.getDocument('Main').getObject('Pad003').Type = 0
    App.getDocument('Main').getObject('Pad003').UpToFace = None
    App.getDocument('Main').getObject('Pad003').Reversed = 0
    App.getDocument('Main').getObject('Pad003').Midplane = 1
    App.getDocument('Main').getObject('Pad003').Offset = 0
    App.getDocument('Main').recompute()
    # Gui.getDocument('Main').resetEdit()
    App.getDocument('Main').getObject('Sketch003').Visibility = False



    
    ### Begin command Part_Cone
    App.ActiveDocument.addObject("Part::Cone","Cone")
    App.ActiveDocument.ActiveObject.Label = "円錐"
    # Object created at document root.
    App.ActiveDocument.recompute()
    # Gui.SendMsgToActiveView("ViewFit")
    ### End command Part_Cone
    # Gui.Selection.addSelection('Main','Cone')
    FreeCAD.getDocument('Main').getObject('Cone').Radius2 = '40 mm'
    FreeCAD.getDocument('Main').getObject('Cone').Radius1 = '0 mm' 
    FreeCAD.getDocument('Main').getObject('Cone').Height = '0 mm'
    FreeCAD.getDocument('Main').getObject('Cone').Height = '50 mm'
    App.getDocument("Main").Cone.Placement=App.Placement(App.Vector(0,0,190), App.Rotation(App.Vector(0,1,0),180), App.Vector(0,0,0))
    # Gui.Selection.clearSelection()
    print("neko----------------------------")
    return "おでんを作成しました"