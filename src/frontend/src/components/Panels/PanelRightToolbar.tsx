import React, { ReactNode } from "react";
import { Body1Strong, Button } from "@fluentui/react-components";
import { DismissRegular } from '@fluentui/react-icons';
import "./Panels.scss"; // Import for styling

interface PanelRightToolbarProps {
    panelTitle?: string | null;
    panelIcon?: ReactNode;
    //   panelType?: "first" | "second"; // Optional, defaults to "first"
    children?: ReactNode;
    handleDismiss?: () => void;  // Add this line
}

const PanelRightToolbar: React.FC<PanelRightToolbarProps> = ({
    panelTitle,
    panelIcon,
    //   panelType = "first", // Default value set here
    children,
    handleDismiss,
}) => {
    return (
        <div
            className="panelToolbar"
        >
            <div
                className="panelTitle"
            >
                {panelIcon && (
                    <div
                        className="panelIcon"
                    >
                        {panelIcon}
                    </div>
                )}
                {panelTitle && (
                    <Body1Strong
                        className="panelSecTitle"
                    >
                        {panelTitle}
                    </Body1Strong>
                )}
            </div>
            <div
                className="panelTools"
            >
                {children}
                <Button
                    appearance="subtle"
                    icon={<DismissRegular />}
                    onClick={handleDismiss} // Handle dismiss logic
                    aria-label="Close panel"
                />
            </div>
        </div>
    );
};

export default PanelRightToolbar;