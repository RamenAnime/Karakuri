// Cradle for the Xbox One Kinect (Kinect v2). Body is 249 x 66 x 67 mm
// and weighs about one kilogram, so the cradle grips the centre 150 mm
// and the rest overhangs each side. Four strap slots take 20 mm hook
// and loop straps to lock the sensor down. Bolts to the tilt wedge or
// straight onto a mast flange with 4 x M4. Print trough opening up,
// supports only under the strap slots.

include <common.scad>

inner_w = 68;     // Kinect 66 plus foam tape
inner_h = 30;     // wall height, grips lower half of the body
cradle_len = 150;
floor_t = 6;
wall = 6;

module kinect_cradle() {
    difference() {
        // Outer shell
        translate([0, 0, 0])
            rounded_plate(inner_w + 2 * wall, cradle_len, floor_t + inner_h, 5);
        // Trough
        translate([0, 0, floor_t])
            linear_extrude(inner_h + 1)
                square([inner_w, cradle_len + 2], center = true);
        // Mast bolt pattern
        four_holes(50, 50, m4, floor_t);
        // Strap slots through the floor beside each wall
        for (sy = [-1, 1], sx = [-1, 1])
            translate([sx * (inner_w / 2 - 6), sy * 48, 0])
                slot(4, 22, floor_t);
        // Ventilation, the Kinect runs warm
        for (y = [-30, 0, 30])
            translate([0, y, 0]) hole(14, floor_t);
    }
}

kinect_cradle();
