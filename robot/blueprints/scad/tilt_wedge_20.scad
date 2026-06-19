// 20 degree tilt wedge between the mast top flange and the camera
// cradle or plate. Tilts the sensor down so the floor 0.5 to 2.0 m
// ahead fills the depth frame. Through holes both faces, 4 x M4.
// Print with the thick end down, no supports.

include <common.scad>

base = 70;
angle = 20;
min_t = 8;

module tilt_wedge() {
    difference() {
        // Wedge body
        hull() {
            linear_extrude(min_t) square([base, base], center = true);
            translate([0, -base / 2, 0])
                rotate([angle, 0, 0])
                    linear_extrude(0.1)
                        translate([0, base / 2]) square([base, base], center = true);
        }
        // Vertical bolt holes through everything
        four_holes(50, 50, m4, base);
    }
}

tilt_wedge();
