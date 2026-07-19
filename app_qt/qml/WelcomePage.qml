import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    anchors.fill: parent

    signal startRequested()

    // Nền gradient trắng -> cam nhạt
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#ffffff" }
            GradientStop { position: 0.65; color: "#fff3e4" }
            GradientStop { position: 1.0; color: "#ffe4c7" }
        }
    }

    // Các bong bóng cam trôi nhẹ làm hiệu ứng nền
    Repeater {
        model: [
            { size: 220, xr: 0.08, yr: 0.16, o: 0.10, dur: 5200 },
            { size: 140, xr: 0.82, yr: 0.10, o: 0.13, dur: 4300 },
            { size: 90,  xr: 0.70, yr: 0.72, o: 0.16, dur: 3600 },
            { size: 260, xr: 0.88, yr: 0.78, o: 0.08, dur: 6000 },
            { size: 60,  xr: 0.22, yr: 0.78, o: 0.20, dur: 3000 }
        ]

        delegate: Rectangle {
            id: bubble
            property real yShift: 0

            width: modelData.size
            height: modelData.size
            radius: width / 2
            color: "#f97316"
            opacity: modelData.o
            x: root.width * modelData.xr - width / 2
            y: root.height * modelData.yr - height / 2 + yShift

            SequentialAnimation on yShift {
                loops: Animation.Infinite
                NumberAnimation { to: -18; duration: modelData.dur; easing.type: Easing.InOutSine }
                NumberAnimation { to: 18; duration: modelData.dur; easing.type: Easing.InOutSine }
            }
        }
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 14
        width: Math.min(560, root.width - 80)

        Text {
            id: logo
            text: "📷"
            font.pixelSize: 64
            Layout.alignment: Qt.AlignHCenter
            opacity: 0
            scale: 0.6
        }

        Text {
            id: title
            text: "AI-English"
            color: "#ea580c"
            font.pixelSize: 42
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            opacity: 0
        }

        Text {
            id: subtitle
            text: "Chào mừng bạn đến với hệ thống nhận diện vật thể\nhỗ trợ học từ vựng tiếng Anh"
            color: "#6b5d4f"
            font.pixelSize: 17
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.3
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            opacity: 0
        }

        Item { Layout.preferredHeight: 14 }

        Button {
            id: startButton
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 220
            implicitHeight: 52
            opacity: 0

            background: Rectangle {
                radius: 26
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: startButton.hovered ? "#fb923c" : "#f97316" }
                    GradientStop { position: 1.0; color: startButton.hovered ? "#f97316" : "#ea580c" }
                }
            }

            contentItem: Text {
                text: "Bắt đầu khám phá  →"
                color: "white"
                font.pixelSize: 17
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            // Nhịp "thở" nhẹ để mời bấm
            SequentialAnimation on scale {
                id: pulseAnim
                running: false
                loops: Animation.Infinite
                NumberAnimation { to: 1.045; duration: 900; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutSine }
            }

            onClicked: {
                pulseAnim.stop()
                root.startRequested()
            }
        }
    }

    // Xuất hiện lần lượt: logo -> tiêu đề -> mô tả -> nút
    SequentialAnimation {
        running: true

        ParallelAnimation {
            NumberAnimation { target: logo; property: "opacity"; to: 1; duration: 420; easing.type: Easing.OutCubic }
            NumberAnimation { target: logo; property: "scale"; from: 0.6; to: 1; duration: 480; easing.type: Easing.OutBack }
        }
        NumberAnimation { target: title; property: "opacity"; to: 1; duration: 360; easing.type: Easing.OutCubic }
        NumberAnimation { target: subtitle; property: "opacity"; to: 1; duration: 360; easing.type: Easing.OutCubic }
        ParallelAnimation {
            NumberAnimation { target: startButton; property: "opacity"; to: 1; duration: 360; easing.type: Easing.OutCubic }
        }
        ScriptAction { script: pulseAnim.start() }
    }
}
