"""Graphics module for game visualization.

The library is designed to make it very easy for programmers to
experiment with computer graphics in an object oriented fashion.

The library provides the following graphical objects:
    Point
    Line
    Circle
    Oval
    Rectangle
    Polygon
    Text
    Entry (for text-based input)
    Image

Various attributes of graphical objects can be set such as
outline-color, fill-color and line-width. Graphical objects also
support moving and hiding for animation effects.
"""

import time
import os
import sys
import tkinter as tk

# Default configuration
DEFAULT_CONFIG = {
    'outline': 'black',
    'fill': '',
    'width': '1',
    'font': ('helvetica', 12, 'normal')
}

class GraphicsObject:
    """Generic base class for all graphics objects"""
    def __init__(self, config):
        self.config = {}
        for option in config:
            self.config[option] = DEFAULT_CONFIG.get(option, "")
        self.canvas = None
        self.id = None

    def setFill(self, color):
        """Set fill color"""
        self._reconfig("fill", color)
        
    def setOutline(self, color):
        """Set outline color"""
        self._reconfig("outline", color)
        
    def setWidth(self, width):
        """Set line weight"""
        self._reconfig("width", width)

    def draw(self, graphwin):
        """Draw the object in graphwin, which should be a GraphWin object"""
        if self.canvas and not self.canvas.isClosed(): raise GraphicsError(OBJ_ALREADY_DRAWN)
        if graphwin.isClosed(): raise GraphicsError("Can't draw to closed window")
        self.canvas = graphwin
        self.id = self._draw(graphwin, self.config)
        if graphwin.autoflush:
            _root.update()

    def undraw(self):
        """Undraw the object"""
        if not self.canvas: return
        if not self.canvas.isClosed():
            self.canvas.delete(self.id)
            if self.canvas.autoflush:
                _root.update()
        self.canvas = None
        self.id = None

    def _reconfig(self, option, setting):
        """Reset the configuration"""
        if option not in self.config:
            raise GraphicsError(UNSUPPORTED_METHOD)
        options = self.config
        options[option] = setting
        if self.canvas and not self.canvas.isClosed():
            self.canvas.itemconfig(self.id, options)

    def getAnchor(self):
        """Return anchor point."""
        return self.anchor

    def move(self, dx, dy):
        """Move object by dx units in x direction and dy units in y direction"""
        self._move(dx, dy)
        if self.canvas and not self.canvas.isClosed():
            x = dx
            y = dy
            if self.canvas.trans:
                x = dx
                y = dy
            self.canvas.move(self.id, x, y)
            if self.canvas.autoflush:
                _root.update()
        return self

    def getX(self):
        """Return x coordinate of anchor point"""
        return self.anchor.getX()

    def getY(self):
        """Return y coordinate of anchor point"""
        return self.anchor.getY()

    def get_id(self):
        """Return the id of the object on the canvas."""
        return self.id

    def isDrawn(self):
        """Check if object is currently drawn."""
        return self.canvas is not None

class GraphicsError(Exception):
    """Generic error class for graphics module exceptions."""
    pass

# Constants
OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"

# Root window setup
_root = tk.Tk()
_root.withdraw()

def update():
    """Update the display."""
    _root.update()

class GraphWin(tk.Canvas):
    """A GraphWin is a toplevel window for displaying graphics."""

    def __init__(self, title="Graphics Window", width=200, height=200, autoflush=True):
        master = tk.Toplevel(_root)
        master.protocol("WM_DELETE_WINDOW", self.close)
        tk.Canvas.__init__(self, master, width=width, height=height)
        self.master.title(title)
        self.pack()
        master.resizable(0, 0)
        self.foreground = "black"
        self.items = []
        self.mouseX = None
        self.mouseY = None
        self.bind("<Button-1>", self._onClick)
        self.bind_all("<Key>", self._onKey)
        self.height = height
        self.width = width
        self.autoflush = autoflush
        self._mouseCallback = None
        self.trans = None
        self.closed = False
        master.lift()
        self.lastKey = ""
        self.keys = []
        
        if autoflush:
            _root.update()

    def enable_key_buffer(self):
        """Enable key buffer for multiple key detection."""
        self.unbind_all("<Key>")
        self.bind_all("<KeyPress>", self._onKeyPress)
        self.bind_all("<KeyRelease>", self._onKeyRelease)
    
    # Alias for Portuguese version
    ligar_Buffer = enable_key_buffer
    
    def disable_key_buffer(self):
        """Disable key buffer and return to single key detection."""
        self.unbind_all("<KeyPress>")
        self.unbind_all("<KeyRelease>")
        self.bind_all("<Key>", self._onKey)
        
    # Alias for Portuguese version
    desligar_Buffer = disable_key_buffer
        
    def check_key_buffer(self):
        """Return list of currently pressed keys."""
        if self.isClosed():
            raise GraphicsError("checkKey in closed window")
        return self.keys 
        
    # Alias for Portuguese version
    checkKey_Buffer = check_key_buffer
    
    def _onKeyPress(self, evnt):
        if not evnt.keysym in self.keys:
            self.keys.append(evnt.keysym)
            
    def _onKeyRelease(self, evnt):
        if evnt.keysym in self.keys:
            self.keys.remove(evnt.keysym)

    def __checkOpen(self):
        if self.closed:
            raise GraphicsError("window is closed")

    def _onKey(self, evnt):
        self.lastKey = evnt.keysym

    def setBackground(self, color):
        """Set background color of the window."""
        self.__checkOpen()
        self.config(bg=color)
        self.__autoflush()

    def close(self):
        """Close the window."""
        if self.closed:
            return
        self.closed = True
        self.master.destroy()
        self.__autoflush()

    def isClosed(self):
        """Check if window is closed."""
        return self.closed

    def isOpen(self):
        """Check if window is open."""
        return not self.closed

    def __autoflush(self):
        if self.autoflush:
            _root.update()

    def getMouse(self):
        """Wait for mouse click and return Point object."""
        self.update()
        self.mouseX = None
        self.mouseY = None
        while self.mouseX == None or self.mouseY == None:
            self.update()
            if self.isClosed():
                raise GraphicsError("getMouse in closed window")
            time.sleep(.1)
        x, y = self.mouseX, self.mouseY
        self.mouseX = None
        self.mouseY = None
        return Point(x, y)

    def checkMouse(self):
        """Return last mouse click or None."""
        if self.isClosed():
            raise GraphicsError("checkMouse in closed window")
        self.update()
        if self.mouseX != None and self.mouseY != None:
            x, y = self.mouseX, self.mouseY
            self.mouseX = None
            self.mouseY = None
            return Point(x, y)
        else:
            return None

    def getKey(self):
        """Wait for user to press a key and return it as a string."""
        self.lastKey = ""
        while self.lastKey == "":
            self.update()
            if self.isClosed():
                raise GraphicsError("getKey in closed window")
            time.sleep(.1)
        key = self.lastKey
        self.lastKey = ""
        return key

    def checkKey(self):
        """Return last key pressed or None."""
        if self.isClosed():
            raise GraphicsError("checkKey in closed window")
        self.update()
        key = self.lastKey
        self.lastKey = ""
        return key

    def getHeight(self):
        """Return the height of the window."""
        return self.height
        
    def getWidth(self):
        """Return the width of the window."""
        return self.width

    def _onClick(self, e):
        self.mouseX = e.x
        self.mouseY = e.y
        if self._mouseCallback:
            self._mouseCallback(Point(e.x, e.y))
            
    def toScreen(self, x, y):
        """Convert world coordinates to screen coordinates."""
        if self.trans:
            return self.trans.screen(x, y)
        else:
            return x, y
            
    def toWorld(self, x, y):
        """Convert screen coordinates to world coordinates."""
        if self.trans:
            return self.trans.world(x, y)
        else:
            return x, y

class Point(GraphicsObject):
    def __init__(self, x, y):
        GraphicsObject.__init__(self, [])
        self.x = x
        self.y = y
        
    def _draw(self, canvas, options):
        x,y = canvas.toScreen(self.x,self.y)
        return canvas.create_rectangle(x,y,x+1,y+1,options)
        
    def _move(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy
        
    def clone(self):
        other = Point(self.x,self.y)
        other.config = self.config.copy()
        return other
                
    def getX(self): return self.x
    def getY(self): return self.y

class _BBox(GraphicsObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.
    
    def __init__(self, p1, p2, options=["outline","width","fill"]):
        GraphicsObject.__init__(self, options)
        self.p1 = p1.clone()
        self.p2 = p2.clone()

    def _move(self, dx, dy):
        self.p1.x = self.p1.x + dx
        self.p1.y = self.p1.y + dy
        self.p2.x = self.p2.x + dx
        self.p2.y = self.p2.y + dy
                
    def getP1(self): return self.p1.clone()

    def getP2(self): return self.p2.clone()
    
    def getCenter(self):
        p1 = self.p1
        p2 = self.p2
        return Point((p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0)
    
class Rectangle(_BBox):
    
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)
    
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        return canvas.create_rectangle(x1,y1,x2,y2,options)
        
    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.config = self.config.copy()
        return other
        
class Oval(_BBox):
    
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)
        
    def clone(self):
        other = Oval(self.p1, self.p2)
        other.config = self.config.copy()
        return other
   
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        return canvas.create_oval(x1,y1,x2,y2,options)
    
class Circle(Oval):
    
    def __init__(self, center, radius):
        p1 = Point(center.x-radius, center.y-radius)
        p2 = Point(center.x+radius, center.y+radius)
        Oval.__init__(self, p1, p2)
        self.radius = radius
        
    def clone(self):
        other = Circle(self.getCenter(), self.radius)
        other.config = self.config.copy()
        return other
        
    def getRadius(self):
        return self.radius
              
class Line(_BBox):
    
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2, ["arrow","fill","width"])
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill
   
    def clone(self):
        other = Line(self.p1, self.p2)
        other.config = self.config.copy()
        return other
  
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.toScreen(p1.x,p1.y)
        x2,y2 = canvas.toScreen(p2.x,p2.y)
        return canvas.create_line(x1,y1,x2,y2,options)
        
    def setArrow(self, option):
        if not option in ["first","last","both","none"]:
            raise GraphicsError(BAD_OPTION)
        self._reconfig("arrow", option)

class Polygon(GraphicsObject):
    
    def __init__(self, *points):
        # if points passed as a list, extract it
        if len(points) == 1 and type(points[0]) == type([]):
            points = points[0]
        self.points = list(map(Point.clone, points))
        GraphicsObject.__init__(self, ["outline", "width", "fill"])
        
    def clone(self):
        other = Polygon(*self.points)
        other.config = self.config.copy()
        return other

    def getPoints(self):
        return list(map(Point.clone, self.points))

    def _move(self, dx, dy):
        for p in self.points:
            p.move(dx,dy)
   
    def _draw(self, canvas, options):
        args = [canvas]
        for p in self.points:
            x,y = canvas.toScreen(p.x,p.y)
            args.append(x)
            args.append(y)
        args.append(options)
        return GraphWin.create_polygon(*args) 

class Text(GraphicsObject):
    
    def __init__(self, p, text):
        GraphicsObject.__init__(self, ["justify","fill","text","font"])
        self.setText(text)
        self.anchor = p.clone()
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill
        self.config["justify"] = "center"  # Set default justification
        
    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        return canvas.create_text(x,y,options)
        
    def _move(self, dx, dy):
        self.anchor.move(dx,dy)
        
    def clone(self):
        other = Text(self.anchor, self.config['text'])
        other.config = self.config.copy()
        return other

    def setText(self,text):
        self._reconfig("text", text)
        
    def getText(self):
        return self.config["text"]
            
    def getAnchor(self):
        return self.anchor.clone()

    def setFace(self, face):
        if face in ['helvetica','arial','courier','times roman']:
            f,s,b = self.config['font']
            self._reconfig("font",(face,s,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 36:
            f,s,b = self.config['font']
            self._reconfig("font", (f,size,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            f,s,b = self.config['font']
            self._reconfig("font", (f,s,style))
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.setFill(color)

class Entry(GraphicsObject):

    def __init__(self, p, width):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        #print self.anchor
        self.width = width
        self.text = tk.StringVar(_root)
        self.text.set("")
        self.fill = "gray"
        self.color = "black"
        self.font = DEFAULT_CONFIG['font']
        self.entry = None

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Entry(frm,
                            width=self.width,
                            textvariable=self.text,
                            bg = self.fill,
                            fg = self.color,
                            font=self.font)
        self.entry.pack()
        #self.setFill(self.fill)
        self.entry.focus_set()
        return canvas.create_window(x,y,window=frm)

    def getText(self):
        return self.text.get()

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def getAnchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Entry(self.anchor, self.width)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def setText(self, t):
        self.text.set(t)

    def setFill(self, color):
        self.fill = color
        if self.entry:
            self.entry.config(bg=color)

    def _setFontComponent(self, which, value):
        f,s,b = self.font
        if which == "family": f = value
        elif which == "size": s = value
        elif which == "style": b = value
        font = (f,s,b)
        self.font = font
        if self.entry:
            self.entry.config(font=font)

    def setFace(self, face):
        if face in ['helvetica','arial','courier','times roman']:
            self._setFontComponent("family", face)
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 36:
            self._setFontComponent("size", size)
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            self._setFontComponent("style", style)
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.color=color
        if self.entry:
            self.entry.config(fg=color)

class Image(GraphicsObject):
    """Image class for loading and displaying game images."""
    
    idCount = 0
    imageCache = {}  # Cache to prevent garbage collection of displayed images
    
    def __init__(self, p, pixmap):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        self.imageId = Image.idCount
        Image.idCount = Image.idCount + 1
        self.img = tk.PhotoImage(file=pixmap, master=_root)
        
    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.toScreen(p.x,p.y)
        self.imageCache[self.imageId] = self.img
        return canvas.create_image(x,y,image=self.img)
        
    def _move(self, dx, dy):
        self.anchor.move(dx,dy)
        
    def drawAt(self, canvas, px, py):
        """Draw image at specific pixel coordinates."""
        self.imageCache[self.imageId] = self.img
        return canvas.create_image(px, py, image=self.img)
        
    def undraw(self):
        """Remove image from display."""
        try:
            del self.imageCache[self.imageId]
            GraphicsObject.undraw(self)
        except KeyError:
            pass
    
    def getWidth(self):
        """Return image width in pixels."""
        return self.img.width()

    def getHeight(self):
        """Return image height in pixels."""
        return self.img.height()
        
    def getPixel(self, x, y):
        """Get pixel RGB color at given (x,y) coordinate"""
        value = self.img.get(x,y) 
        if type(value) ==  type(0):
            return [value, value, value]
        else:
            return list(value[:3])

def color_rgb(r, g, b):
    """Convert RGB values to color string."""
    return "#%02x%02x%02x" % (r, g, b)