import rclpy
from rclpy.node import Node
from ai_msgs.msg import PerceptionTargets
from sensor_msgs.msg import CompressedImage
from pymycobot import MyCobot280RDKX5,utils
import time
import cv2
import numpy as np
class MinimalSubscriber(Node):
    def __init__(self):
        self.mc=MyCobot280RDKX5("/dev/ttyS1",1000000)
        self.mc.set_fresh_mode(0)
        self.mc.sync_send_angles([0,0,0,0,0,46.3],100)
        print("ok")
        super().__init__('minimal_subscriber')

        self.cam_subscription = self.create_subscription(
            CompressedImage,
            '/image',  
            self.cam_listener_callback,
            10)

        self.subscription = self.create_subscription(
            PerceptionTargets,
            'hobot_hand_gesture_detection',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        
        
        self.value=None
        self.img=None
        self.count=0
        # self.lock = threading.Lock()

    def cam_listener_callback(self, msg):
       
        np_arr = np.frombuffer(msg.data, np.uint8)
        cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        self.img=cv_image
     
    def listener_callback(self, msg):
        
        for target in msg.targets:
            for attribute in target.attributes:
                self.get_logger().info(f'Value: "{attribute.value}"')
                # self.get_logger().info(f'confidence: "{attribute.confidence}"')
                tmp=int(attribute.value)
                self.count+=1
                #print (f"count={self.count}")
                if self.count==50 and tmp==self.value:
                    if self.value==5:
                        self.mc.send_angles([0,0,0,0,0,46.3],100)
                        time.sleep(1)
                        self.mc.send_angles([0, -15.99, -49.57, 67.93, 7.99, 46.3],100)
                        time.sleep(1)
                        # self.mc.sync_send_angles([0, 30.58, -49.57, 12.48, 21.44, 0],100)
                        # time.sleep(1)
                        self.mc.send_angles([0,0,0,0,0,46.3],100)
                        time.sleep(1)
                        # self.value=None
                    elif self.value==3:
                        if self.img is not None:
                            cv2.imshow("Compressed Image", self.img)
                            cv2.waitKey(2000)
                            cv2.destroyAllWindows()
                            # self.value=None

                    elif self.value==11:
                        for i in range(1):
                            self.mc.send_angles([0, 0, 0, -70, 0, 46.3],100)
                            time.sleep(1)
                            self.mc.send_angles([0, 0, 0, 0, 0, 46.3],100)
                            time.sleep(1)
                            # self.value=None
                    elif self.value==12:
                        self.mc.send_angles([0, -15.99, -49.57, 67.93, 7.99, 46.3],100)
                        time.sleep(1)
                        self.mc.send_angles([-30.58, -45.61, -0.96, 47.37, 38.84, 46.3],100)
                        time.sleep(1)
                    elif self.value==13:
                        self.mc.send_angles([0, -15.99, -49.57, 67.93, 7.99, 46.3],100)
                        time.sleep(1)
                        self.mc.send_angles([34.36, -6.24, -63.1, 69.96, -26.27, 46.3],100)
                        time.sleep(1)

                    elif self.value==2:
                        self.mc.send_angles([0, -15.99, -49.57, 67.93, 7.99, 46.3],100)
                        time.sleep(1)
                        self.mc.send_angles([0.79, -13.35, -28.38, 37.7, 7.47, 46.3],100)
                        time.sleep(1)

                    elif self.value==4:
                        self.mc.send_angles([0.7, 48.33, -113.55, 61.43, 0.0, 46.3],100)
                        time.sleep(1)

                    elif self.value==14:
                        self.mc.send_angles([0.7, 48.33, -113.55, 61.43, 0.0, 46.3],100)
                        time.sleep(1)
                        for i in range(3):
                            self.mc.send_angles([0.7, 48.33, -113.55, 61.43, 0.0, 46.3],100)
                            self.mc.send_angles([0.7, 33.92, -77.34, 38.4, 0.08, 46.3],100)
                        self.mc.send_angles([0.7, 33.92, -77.34, 38.4, 0.08, 46.3],100)
                        time.sleep(2)
                       
                    self.count=0


                self.value=tmp
                if self.count>50:
                    self.count=0

def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

