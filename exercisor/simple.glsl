/* 
simple.glsl
*/
---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3  v_pos;
attribute vec3  v_normal;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;
uniform vec3 sphere_center;

varying vec4 normal_vec;
varying vec4 vertex_pos;
varying vec4 sphere_cen;

void main (void) {
    //compute vertex position in eye_space and normalize normal vector
    vec4 pos = modelview_mat * vec4(v_pos, 1.0);
    vertex_pos = pos;
    normal_vec = vec4(v_normal, 0.0);
    sphere_cen = modelview_mat * vec4(sphere_center, 1.0);
    gl_Position = projection_mat * pos;
}

---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 normal_vec;
varying vec4 vertex_pos;
varying vec4 sphere_cen;

uniform mat4 normal_mat;
uniform vec3 diffuse_light;
uniform vec3 ambient_light;
uniform vec3 object_color;

uniform float sphere_radius;
uniform vec3 sphere_color;

void main (void) {
    //correct normal, and compute light vector (assume light at the eye)
    vec4 v_normal = normalize(normal_mat * normal_vec);
    vec4 v_light = normalize(vec4(0, 0, 0, 1) - vertex_pos);

    float diff = max(dot(v_normal, v_light), 0.0);
    vec3 diffuse = diff * diffuse_light;
    vec3 ambient = 0.8 * ambient_light;

    vec3 color = (ambient + diffuse) * object_color;

    float dist = distance(vertex_pos, sphere_cen);

    // if (dist < float(0.1)){
    //     color = (ambient + diffuse) * vec3(0.8157, 0.8863, 0.1647);
    // } else if (dist < float(0.2)) {
    //     color = (ambient + diffuse) * vec3(0.3333, 0.8863, 0.1647);
    // } else if (dist < float(0.5)) {
    //     color = (ambient + diffuse) * vec3(0.1647, 0.8392, 0.8863);
    // } else if (dist < float(1)) {
    //     color = (ambient + diffuse) * vec3(0.6588, 0.1647, 0.8863);
    // } else if (dist < float(2)) {
    //     color = (ambient + diffuse) * vec3(0.8863, 0.1647, 0.3451);
    // } else if (dist < float(3)) {
    //     color = (ambient + diffuse) * vec3(0.749, 0.7451, 0.7882);
    // }

    if (dist < sphere_radius) {
        color = (ambient + diffuse) * sphere_color;
    }

    gl_FragColor = vec4(color, 1);
}
