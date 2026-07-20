import QtQuick
import QtQuick.Layouts

Rectangle {
    id: card
    color: "#FFFFFF"
    radius: 14
    border.color: "#E8E8E8"
    border.width: 1

    // Very light shadow for depth while keeping the UI minimal.
    layer.enabled: true
    layer.smooth: true
}
