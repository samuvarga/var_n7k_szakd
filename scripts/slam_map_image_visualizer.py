#!/usr/bin/env python3

import struct

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2, PointField


class SlamMapPointCloudVisualizer(Node):
    def __init__(self):
        super().__init__('slam_map_pointcloud_visualizer')
        map_qos = QoSProfile(depth=1)
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        pointcloud_qos = QoSProfile(depth=1)
        pointcloud_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        pointcloud_qos.reliability = ReliabilityPolicy.RELIABLE
        self.pointcloud_publisher = self.create_publisher(
            PointCloud2,
            '/slam_map_pointcloud',
            pointcloud_qos,
        )
        self.map_subscription = self.create_subscription(
            OccupancyGrid,
            '/map',
            self._publish_pointcloud,
            map_qos,
        )

    def _publish_pointcloud(self, map_message: OccupancyGrid):
        points = bytearray()
        resolution = map_message.info.resolution
        origin_x = map_message.info.origin.position.x
        origin_y = map_message.info.origin.position.y
        for index, value in enumerate(map_message.data):
            if 0 <= value < 65:
                continue
            column = index % map_message.info.width
            row = index // map_message.info.width
            points.extend(struct.pack(
                '<ffff',
                origin_x + (column + 0.5) * resolution,
                origin_y + (row + 0.5) * resolution,
                0.02,
                float(value),
            ))

        cloud = PointCloud2()
        cloud.header = map_message.header
        cloud.height = 1
        cloud.width = len(points) // 16
        cloud.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
        ]
        cloud.is_bigendian = False
        cloud.point_step = 16
        cloud.row_step = len(points)
        cloud.data = points
        cloud.is_dense = False
        self.pointcloud_publisher.publish(cloud)


def main(args=None):
    rclpy.init(args=args)
    node = SlamMapPointCloudVisualizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()