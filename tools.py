"""Browser-side view capture helpers.

The original module moved the operating-system mouse with PyAutoGUI and took
fixed desktop screenshots.  This version asks Chrome to rotate the whole cube
and captures the browser viewport directly, so neither operation touches the
user's pointer or depends on desktop coordinates.
"""

from pathlib import Path


class Screen:
    """Save the 600 x 600 recognition images supplied by WebDriver."""

    def __init__(
        self,
        controller,
        cube_side=600,
        fallback_offset_y=100,
        image_directory=None,
    ):
        self.controller = controller
        self.cube_side = int(cube_side)
        self.fallback_offset_y = int(fallback_offset_y)
        if image_directory is None:
            image_directory = Path(__file__).resolve().parent / "Image"
        self.image_directory = Path(image_directory)

    def screen_shot(self, index):
        """Capture one cube view through Chrome rather than the desktop."""

        target = self.image_directory / "{}.jpg".format(int(index))
        return self.controller.capture_cube_image(
            target,
            cube_side=self.cube_side,
            fallback_offset_y=self.fallback_offset_y,
        )


def get_image(controller, screen=None):
    """Capture the four solver views using direct whole-cube page rotations.

    The sequence is equivalent to the old up/down/right mouse gestures and
    finishes at exactly the same visual orientation at which it started.
    ``rotate_view`` waits for each page animation, so fixed ``sleep(0.5)`` calls
    are no longer necessary.
    """

    if screen is None:
        screen = Screen(controller)

    screen.screen_shot(0)

    # Old mouse.up_turning(): the old front face moves to the top.
    controller.rotate_view("x", -1)
    screen.screen_shot(1)

    # Old mouse.down_turning(); mouse.right_turning()
    controller.rotate_view("x", 1)
    controller.rotate_view("y", 1)
    screen.screen_shot(2)

    # Old mouse.right_turning()
    controller.rotate_view("y", 1)
    screen.screen_shot(3)

    # Restore the initial view (four positive Y quarter-turns in total).
    controller.rotate_view("y", 2)

    return [screen.image_directory / "{}.jpg".format(index) for index in range(4)]
