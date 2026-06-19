// Universal camera plate. Centre 1/4-20 hole fits any tripod mount
// camera, including the OAK-D Lite, which is the recommended lighter
// alternative to the Kinect. Side M3 grid fits RealSense brackets and
// breakout cameras. Bolts to the wedge or mast with 4 x M4.

include <common.scad>

module camera_plate() {
    difference() {
        rounded_plate(70, 70, 6, 6);
        four_holes(50, 50, m4, 6);
        hole(quarter_inch, 6);
        for (x = [-15, 15], y = [-15, 15])
            translate([x, y, 0]) hole(m3, 6);
        for (y = [-25, 25])
            translate([0, y, 0]) slot(m3, 12, 6);
    }
}

camera_plate();
