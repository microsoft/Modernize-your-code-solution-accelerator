import React, { useState, useEffect, ReactElement } from "react";
import { Toolbar, ToggleButton, ToggleButtonProps } from "@fluentui/react-components";
import eventBus from "../eventbus.js";

type PanelRightTogglesProps = {
  children: React.ReactNode;
};

const PanelRightToggles: React.FC<PanelRightTogglesProps> = ({ children }) => {
  const [activePanel, setActivePanel] = useState<"first" | "second" | "third" | "fourth" | null>(null);

  const panelTypes = ["first", "second", "third", "fourth"] as const;

  useEffect(() => {
    const handlePanelToggle = (panel: "first" | "second" | "third" | "fourth" | null) => {
      setActivePanel(panel);
    };

    // Listen for panel toggle events
    eventBus.on("setActivePanel", handlePanelToggle);

    // Default active panel
    eventBus.emit("setActivePanel", "first");

    return () => {
      eventBus.off("setActivePanel", handlePanelToggle);
    };
  }, []);

  const togglePanel = (panel: "first" | "second" | "third" | "fourth" | null) => {
    eventBus.emit("setActivePanel", activePanel === panel ? null : panel);
  };

  // Type guard to ensure child is a valid ToggleButton
  const isToggleButton = (child: React.ReactNode): child is ReactElement<ToggleButtonProps> => {
    return React.isValidElement(child) && child.type === ToggleButton;
  };

  return (
    <Toolbar style={{ padding: "4px 0", display: "flex", flexDirection: "row-reverse" }}>
      {React.Children.map(children, (child, index) => {
        const panelType = panelTypes[index]; // Dynamically assign panelType based on index
        if (isToggleButton(child) && panelType) {
          return React.cloneElement(child, {
            onClick: () => togglePanel(panelType),
            checked: activePanel === panelType,
          });
        }
        return child; // Return child as is if it doesn't pass the type guard
      })}
    </Toolbar>
  );
};

export default PanelRightToggles;
