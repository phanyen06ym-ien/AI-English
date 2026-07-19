import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: shell
    anchors.fill: parent

    property int pageIndex: 0

    // Thứ tự phải khớp 1-1 với các trang trong StackLayout bên dưới:
    // 0 ImagePage, 1 WebcamPage, 2 VocabularyPage, 3 HistoryPage, 4 StatsPage
    readonly property var navItems: [
        { label: "🖼  Nhận diện ảnh", hint: "Chọn ảnh để nhận diện vật thể" },
        { label: "🎥  Webcam", hint: "Nhận diện trực tiếp qua webcam" },
        { label: "📚  Từ vựng", hint: "Tra cứu danh sách từ vựng" },
        { label: "🕘  Lịch sử", hint: "Xem lại các lượt nhận diện" },
        { label: "📊  Thống kê", hint: "Tiến độ học từ vựng" }
    ]

    // currentIndex đổi ngay lập tức cùng lúc với pageIndex (không qua biến trung
    // gian/độ trễ animation nào) để tránh cảnh sidebar đã tô sáng mục mới nhưng
    // nội dung bên phải vẫn còn hiện trang cũ.
    onPageIndexChanged: {
        if (pageIndex === 3) historyController.refresh()
        if (pageIndex === 4) statsController.refresh()
        pageFadeAnim.restart()
    }

    NumberAnimation {
        id: pageFadeAnim
        target: stack
        property: "opacity"
        from: 0
        to: 1
        duration: 180
        easing.type: Easing.OutCubic
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 230
            Layout.fillHeight: true
            color: "#ffffff"

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: "#f1e3d3"
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 6

                Text {
                    text: "AI-English"
                    color: "#ea580c"
                    font.pixelSize: 22
                    font.bold: true
                }

                Text {
                    text: "Học tiếng Anh qua nhận diện vật thể"
                    color: "#a4988a"
                    font.pixelSize: 11
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    Layout.bottomMargin: 16
                }

                Item {
                    id: navContainer
                    Layout.fillWidth: true
                    implicitHeight: navColumn.implicitHeight

                    Rectangle {
                        id: activeIndicator
                        width: 4
                        height: 46
                        radius: 2
                        color: "#f97316"
                        x: 0
                        y: shell.pageIndex * (46 + navColumn.spacing)
                        Behavior on y { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                    }

                    ColumnLayout {
                        id: navColumn
                        anchors.fill: parent
                        spacing: 6

                        Repeater {
                            model: shell.navItems

                            delegate: SidebarButton {
                                Layout.fillWidth: true
                                text: modelData.label
                                hint: modelData.hint
                                active: shell.pageIndex === index
                                onClicked: shell.pageIndex = index
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    text: shell.navItems[shell.pageIndex].hint
                    color: "#a4988a"
                    font.pixelSize: 11
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            StackLayout {
                id: stack
                anchors.fill: parent
                currentIndex: shell.pageIndex

                ImagePage {}
                WebcamPage {}
                VocabularyPage {}
                HistoryPage {}
                StatsPage {}
            }
        }
    }
}
