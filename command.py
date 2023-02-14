import cv2 as cv
import color_histogram_feature_extraction
import knn_classifier
import kociemba


color_dict = {"red": 'F', "orange": 'B', "yellow": 'D', "green": 'L', "blue": 'R', "white": 'U'}

color_list = []

side = 30

offset0 = 87
offset1 = 90
offset2x = 80
offset2y = 45


def get_color_0(img):
    x0 = int(img.shape[0] / 7)
    y0 = int(img.shape[1] / 3 + 5)

    for i in range(3):
        yy0 = y0
        xx0 = x0
        yy0 += offset0 * i
        for j in range(3):
            box = img[yy0:yy0 + side, xx0:xx0 + side]
            color_histogram_feature_extraction.color_histogram_of_test_image(box)
            color = knn_classifier.main('training.data', 'test.data')
            color_list.append(color_dict[color])
            xx0 += side + 50
            yy0 += side + 17


def get_color_1(img):
    x1 = int(img.shape[0] / 2) + side
    y1 = int(img.shape[1] / 2)

    for i in range(3):
        yy1 = y1
        xx1 = x1
        yy1 += offset1 * i
        for j in range(3):
            box = img[yy1:yy1 + side, xx1:xx1 + side]
            color_histogram_feature_extraction.color_histogram_of_test_image(box)
            color = knn_classifier.main('training.data', 'test.data')
            color_list.append(color_dict[color])
            xx1 += side + 45
            yy1 -= side + 20


def get_color_2(img):
    x2 = int(img.shape[0] / 2 - side / 2)
    y2 = int(img.shape[1] / 8 - side)

    for i in range(3):
        xx2 = x2
        yy2 = y2
        xx2 -= offset2x * i
        yy2 += offset2y * i
        for j in range(3):
            box = img[yy2:yy2 + side, xx2:xx2 + side]
            color_histogram_feature_extraction.color_histogram_of_test_image(box)
            color = knn_classifier.main('training.data', 'test.data')
            color_list.append(color_dict[color])
            xx2 += side + 50
            yy2 += side + 15


def get_color_123(img):
    get_color_2(img)
    get_color_1(img)
    get_color_0(img)


def get_color_list():
    img = cv.imread("./Image/0.jpg")
    get_color_123(img)

    for i in range(3):
        img = cv.imread("./Image/{}.jpg".format(i+1))
        get_color_0(img)


def command():
    get_color_list()
    return kociemba.solve(''.join(color_list))


if __name__ == '__main__':
    # cap = cv2.VideoCapture("http://admin@admin/192.168.43.1:8081")
    get_color_list()
    print(color_list)
    # print(str(color_list))
    # print("".join(color_list))
    print(kociemba.solve(''.join(color_list)))
    # print(func(frame))


