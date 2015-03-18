//
//  AppDelegate.h
//  CS191Client
//
//  Created by Saurabh Sharan on 3/7/15.
//  Copyright (c) 2015 Saurabh Sharan. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface AppDelegate : UIResponder <UIApplicationDelegate, NSStreamDelegate>
{
    NSInputStream *inputStream;
    NSOutputStream *outputStream;
}

@property (strong, nonatomic) UIWindow *window;


@end

