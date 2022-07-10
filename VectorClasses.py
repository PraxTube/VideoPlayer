class IntVector2:
    """Provide the functionality of a Vector2 for integer."""
    def __init__(self, x, y):
        """Initialise x and y if they are integer."""
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Numbers need to be of type integer", (x, y))
        self.x = x
        self.y = y

    def __str__(self):
        """Return a string with the format (x, y)."""
        return "({}, {})".format(self.x, self.y)

    def __getitem__(self, i):
        """Provide the ability to index x and y through indexing."""
        if type(i) != int:
           raise TypeError("Index not an integer", i)
        if i == 0:
           return self.x
        elif i == 1:
           return self.y
        raise IndexError("Index outside of range", i)

    def __add__(self, other):
        """Add two IntVector2 instances together, else raise error."""
        if not isinstance(other, IntVector2):
            raise TypeError("Cannot \'{}\' type \'{}\' with \'{}\'".format("+", type(self), type(other)), other)
        return IntVector2(self.x + other.x, self.y + other.y)

    def __mul__(self, other):
        """Calculate dot-product or scale IntVector2, depending on other."""
        if isinstance(other, IntVector2):
            return self.x * other.x + self.y * other.y
        if isinstance(other, int):
            return IntVector2(self.x * other, self.y * other)
        if isinstance(other, float):
            return IntVector2(int(self.x * other), int(self.y * other))
        raise TypeError("Cannot \'{}\' type \'{}\' with \'{}\'".format("*", type(self), type(other)), other)

    def __rmul__(self, other):
        """Calculate dot-product or scale IntVector2, depending on other."""
        if isinstance(other, IntVector2):
            return self.x * other.x + self.y * other.y
        if isinstance(other, int):
            return IntVector2(self.x * other, self.y * other)
        if isinstance(other, float):
            return IntVector2(int(self.x * other), int(self.y * other))
        raise TypeError("Cannot \'{}\' type \'{}\' with \'{}\'".format("*", type(self), type(other)), other)

    def copy(self):
        """Copy self by creating a new instance with same values."""
        return IntVector2(self.x, self.y)
